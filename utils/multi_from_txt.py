"""
脚本介绍：
    用 sherpa-onnx 生成的字幕，总归是会有一些缺陷
    例如有错字，分句不准
    
    所以除了自动生成的 srt 文件
    还额外生成了 txt 文件（每行一句），和 json 文件（包含每个字的时间戳）
    
    用户可以在识别完成后，手动修改 txt 文件，更正少量的错误，正确地分行
    然后调用这个脚本，处理 txt 文件
    
    脚本会找到同文件名的 json 文件，从里面得到字级时间戳，再按照 txt 里面的分行，
    生成正确的 srt 字幕
"""

import json
import logging
import re
from collections import deque
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Dict, Union, NamedTuple

import srt
import typer
from rich import print


class Config(NamedTuple):
    threshold: int = 8
    tolerance: int = 5
    scout_num: int = 5


config = Config()


@dataclass
class Scout:
    hit: int = 0
    miss: int = 0
    score: int = 0
    start: int = 0
    text: str = ''


def get_scout(line, words, cursor, config: Config = config):
    # 使用更高效的数据结构
    scout_list = deque(maxlen=6)  # 限制最大长度为6，避免无限增长

    # 预处理 line，避免重复操作
    processed_line = re.sub('[,.?:%，。？、\s\d]', '', line.lower())

    # 使用 set 来加速查找
    line_chars = set(processed_line)

    words_num = len(words)  # 定义 words_num

    for _ in range(config.scout_num):
        # 新建一个侦察兵
        scout = Scout()
        scout.text = processed_line

        # 找到起始点
        while cursor < words_num and scout.text and words[cursor]['word'] not in scout.text:
            cursor += 1
        scout.start = cursor

        # 如果到末尾了，就不必侦察了
        if cursor == words_num:
            break

        # 开始侦察，容错5个词，查找连续匹配
        tolerance = config.tolerance
        current_cursor = cursor
        while current_cursor < words_num and tolerance:
            if words[current_cursor]['word'].lower() in line_chars:
                scout.text = scout.text.replace(words[current_cursor]['word'].lower(), '', 1)
                scout.hit += 1
                current_cursor += 1
                tolerance = config.tolerance
            else:
                if words[current_cursor]['word'] not in '零一二三四五六七八九十百千万幺两点时分秒之':
                    tolerance -= 1
                    scout.miss += 1
                current_cursor += 1
            if not scout.text:
                break

        # 侦查完毕，带着得分入列
        scout.score = scout.hit - scout.miss
        scout_list.append(scout)

        # 如果侦查分优秀，步进一步再重新细勘
        if scout.hit >= 2:
            cursor = scout.start + 1

    # 使用 max 函数找到最佳 scout
    return max(scout_list, key=lambda x: x.score) if scout_list else None


def lines_match_words(text_lines: List[str], words: List[Dict[str, Union[str, float]]],
                      match_config: Config = config) -> \
        tuple[List[srt.Subtitle], List[str]]:
    """
    将文本行与单词列表匹配，生成字幕列表。

    Args:
        text_lines (List[str]): 文本行列表。
        words (List[Dict[str, Union[str, float]]]): 单词信息列表。

    Returns:
        List[srt.Subtitle]: 生成的字幕列表。
        :param text_lines: 
        :param words: 
        :param match_config: 
    """
    # 空的字幕列表
    subtitle_list = []
    # 存储时间戳和文本的列表，用于后续写入main.txt文件
    main_txt_content = []

    cursor = 0  # 索引，指向最新已确认的下一个
    words_num = len(words)  # 词数，结束条件
    for index, line in enumerate(text_lines):

        # 先清除空行
        if not line.strip():
            continue

        # 侦察前方，得到起点、评分
        scout = get_scout(line, words, cursor, match_config)
        if scout is None:  # 没有结果表明出错，应提前结束
            print('字幕匹配出现错误')
            break
        cursor, score = scout.start, scout.score

        # 避免越界
        if cursor >= words_num:
            break

        # 初始化
        temp_text = re.sub('[,.?，。？、\s]', '', line.lower())
        t1 = words[cursor]['start']
        t2 = words[cursor]['end']
        threshold = match_config.threshold

        # 开始匹配
        probe = cursor  # 重置探针
        while (probe - cursor < threshold):
            if probe >= words_num:
                break  # 探针越界，结束
            w = words[probe]['word'].lower().strip(' ,.?!，。？！@')
            t3 = words[probe]['start']
            t4 = words[probe]['end']
            probe += 1
            if w in temp_text:
                temp_text = temp_text.replace(w, '', 1)
                t2 = t4  # 延长字幕结束时间
                cursor = probe
                if not temp_text:
                    break  # 如果 temp 已清空,则代表本条字幕已完

        # 新建字幕
        subtitle = srt.Subtitle(index=index,
                                content=line,
                                start=timedelta(seconds=t1),
                                end=timedelta(seconds=t2))
        # 收集时间戳和文本内容，将时间戳格式化为整数秒
        integer_time = int(t1)  # 取整数秒部分
        main_txt_content.append(f'{integer_time} {line}')

        subtitle_list.append(subtitle)

        # 如果本轮侦察评分不优秀，下一句应当回溯，避免本句识别末尾没刹住
        if score <= 0:
            cursor = max(0, cursor - 20)

    # 不在这里写入文件，而是返回内容列表，由调用函数决定如何处理
    return subtitle_list, main_txt_content


def get_words(json_file: Path) -> List[Dict[str, Union[str, float]]]:
    """
    从JSON文件中读取单词信息。

    Args:
        json_file (Path): JSON文件的路径。

    Returns:
        List[Dict[str, Union[str, float]]]: 包含单词信息的字典列表。
    """
    # 读取分词 json 文件
    with open(json_file, 'r', encoding='utf-8') as f:
        json_info = json.load(f)

    # 获取带有时间戳的分词列表
    words = [{'word': token.replace('@', ''), 'start': timestamp, 'end': timestamp + 0.2}
             for (timestamp, token) in zip(json_info['timestamps'], json_info['tokens'])]
    for i in range(len(words) - 1):
        words[i]['end'] = min(words[i]['end'], words[i + 1]['start'])

    return words


def get_lines(txt_file: Path) -> List[str]:
    # 读取分好行的字幕
    with open(txt_file, 'r', encoding='utf-8') as f:
        text_lines = f.readlines()
    return text_lines


def one_task(media_file: Path) -> Optional[Path]:
    try:
        # 配置要打开的文件
        txt_file = media_file.with_suffix('.txt')
        json_file = media_file.with_suffix('.json')
        srt_file = media_file.with_suffix('.srt')

        # 生成与原文件同样前缀的main.txt文件名
        file_stem = media_file.stem  # 获取文件名（无后缀）
        main_txt_file = media_file.parent / f"{file_stem}.main.txt"

        if (not txt_file.exists()) or (not json_file.exists()):
            print(f'无法找到 {media_file}对应的txt、json文件，跳过')
            return None

        # 获取带有时间戳的分词列表，获取分行稿件，匹配得到 srt 
        words = get_words(json_file)
        text_lines = get_lines(txt_file)
        subtitle_list, main_txt_content = lines_match_words(text_lines, words)  # 现在函数同时返回字幕列表和main.txt内容

        if not main_txt_content:
            print('警告：main_txt_content列表为空，没有内容可写入')

        # 写入 srt 文件 ！ 重要 ！ ！ ！ 
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(srt.compose(subtitle_list))

        # 确保main.txt文件的父目录存在
        main_txt_file.parent.mkdir(parents=True, exist_ok=True)

        # 创建并写入 main.txt 文件
        print(f'写入文件到：{main_txt_file}')
        with open(main_txt_file, 'w', encoding='utf-8') as f:
            content = '\n'.join(main_txt_content) + '\n'
            f.write(content)
            print(f'写入内容长度：{len(content)}字节')
            print(f'样例内容：{main_txt_content[0] if main_txt_content else "(空)"}')

        return srt_file
    except Exception as e:
        logging.error(f"处理 {media_file} 时出错: {str(e)}")
        return None


def main(files: List[Path]):
    for file in files:
        result = one_task(file)
        if result:
            logging.info(f'写入完成：{result}')
        else:
            logging.warning(f'处理 {file} 失败')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    typer.run(main)

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


def lines_match_words(text_lines: List[str], words: List[Dict[str, Union[str, float]]], config: Config = config) -> \
        List[srt.Subtitle]:
    """
    将文本行与单词列表匹配，生成字幕列表。

    Args:
        text_lines (List[str]): 文本行列表。
        words (List[Dict[str, Union[str, float]]]): 单词信息列表。

    Returns:
        List[srt.Subtitle]: 生成的字幕列表。
    """
    # 空的字幕列表
    subtitle_list = []

    cursor = 0  # 索引，指向最新已确认的下一个
    words_num = len(words)  # 词数，结束条件
    for index, line in enumerate(text_lines):

        # 先清除空行
        if not line.strip():
            continue

        # 侦察前方，得到起点、评分
        scout = get_scout(line, words, cursor, config)
        if scout is None:  # 没有结果表明出错，应提前结束
            print('字幕匹配出现错误')
            break
        cursor, score = scout.start, scout.score

        # tokens = ''.join([x['word'] for x in words[cursor:cursor+50]])
        # print(f'{line=}\n{tokens=}\n{score=}\n{cursor=}\n\n')

        # 避免越界
        if cursor >= words_num:
            break

        # 初始化
        temp_text = re.sub('[,.?，。？、\s]', '', line.lower())
        t1 = words[cursor]['start']
        t2 = words[cursor]['end']
        threshold = config.threshold

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
        subtitle_list.append(subtitle)

        # 如果本轮侦察评分不优秀，下一句应当回溯，避免本句识别末尾没刹住
        if score <= 0:
            cursor = max(0, cursor - 20)

    return subtitle_list


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
        if (not txt_file.exists()) or (not json_file.exists()):
            print(f'无法找到 {media_file}对应的txt、json文件，跳过')
            return None

        # 获取带有时间戳的分词列表，获取分行稿件，匹配得到 srt 
        words = get_words(json_file)
        text_lines = get_lines(txt_file)
        subtitle_list = lines_match_words(text_lines, words)

        # 写入 srt 文件 ！ 重要 ！ ！ ！ 
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(srt.compose(subtitle_list))
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

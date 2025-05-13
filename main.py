import json
import os
import subprocess
import sys
from datetime import datetime

from utils.common_utils import clean_url
from utils.file_downloader import download_video_as_wav
from utils.file_manager import (
    get_today_folder, get_next_file_number, get_temp_dir,
    clean_filename, move_temp_file_to_destination, clean_temp_directory
)


def process_video(url):
    cleaned_url = clean_url(url)
    print(f"清理后的URL: {cleaned_url}")

    # 保存原始 URL和清理后的URL
    url_info = {
        "original_url": url,
        "cleaned_url": cleaned_url
    }

    today_folder = get_today_folder()
    temp_dir = get_temp_dir()
    if temp_dir is None or not os.path.exists(temp_dir):
        print("Error: Unable to create or access temporary directory.")
        return

    file_number = get_next_file_number(today_folder)

    try:
        temp_filename = os.path.join(temp_dir, 'temp_audio')
        title = download_video_as_wav(cleaned_url, temp_filename)
        date_str = datetime.now().strftime('%Y%m%d')
        safe_title = clean_filename(title)
        new_filename = f"{file_number}.{safe_title}_{date_str}.wav"
        full_output_path = os.path.join(today_folder, new_filename)

        try:
            move_temp_file_to_destination(temp_filename, temp_dir, full_output_path)
            print(f"音频成功下载并保存为 {full_output_path}")

            # 保存URL信息到与音频文件相同名称的JSON文件
            base_name = os.path.splitext(full_output_path)[0]  # 获取不含后缀的文件名
            url_json_file = f"{base_name}.audio_urls.json"
            with open(url_json_file, 'w', encoding='utf-8') as f:
                json.dump(url_info, f, ensure_ascii=False, indent=2)
            print(f"已保存URL信息到 {url_json_file}")

            # 调用处理音频文件的脚本
            subprocess.run(["python", "process_audio_file.py", full_output_path])
        except FileNotFoundError as e:
            print(f"错误: {str(e)}")

    except Exception as e:
        print(f"处理失败: {str(e)}")
    finally:
        clean_temp_directory(temp_dir)


def main(url=None):
    if url is None:
        print("欢迎使用视频下载器和转录器！")
        url = input("请输入哔哩哔哩视频链接：")
    process_video(url)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()

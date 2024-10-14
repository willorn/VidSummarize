from utils.downloader import download_video_as_wav
from utils.file_manager import get_today_folder, get_temp_dir, organize_old_files, get_next_file_number
from utils.common_utils import clean_url
from utils.transcriber import transcribe_audio
import os
import shutil
from datetime import datetime
import re


def main():
    print("欢迎使用视频下载器和转录器！")
    organize_old_files()
    url = input("请输入哔哩哔哩视频链接：")
    cleaned_url = clean_url(url)
    print(f"清理后的URL: {cleaned_url}")

    today_folder = get_today_folder()
    temp_dir = get_temp_dir()
    file_number = get_next_file_number(today_folder)

    try:
        temp_filename = os.path.join(temp_dir, 'temp_audio')
        title = download_video_as_wav(cleaned_url, temp_filename)
        date_str = datetime.now().strftime('%Y%m%d')
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)  # 移除文件名中的非法字符
        new_filename = f"{file_number}.{safe_title}_{date_str}.wav"
        full_output_path = os.path.join(today_folder, new_filename)

        # 查找并重命名临时文件
        temp_file = f"{temp_filename}.wav"
        if os.path.exists(temp_file):
            shutil.move(temp_file, full_output_path)
        else:
            print(f"警告：找不到临时文件 {temp_file}")
            # 尝试查找其他可能的临时文件名
            for file in os.listdir(temp_dir):
                if file.startswith(os.path.basename(temp_filename)) and file.endswith('.wav'):
                    shutil.move(os.path.join(temp_dir, file), full_output_path)
                    break
            else:
                raise FileNotFoundError(f"无法找到下载的音频文件")

        print(f"音频已成功下载并保存为 {full_output_path}")

        # 转录音频为文本
        txt_output_path = os.path.splitext(full_output_path)[0] + '.txt'
        transcribe_audio(full_output_path, txt_output_path)
        print(f"音频已成功转录为文本并保存为 {txt_output_path}")

    except Exception as e:
        print(f"处理失败：{str(e)}")
    finally:
        # 清理临时目录
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))


if __name__ == "__main__":
    main()

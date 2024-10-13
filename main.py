import yt_dlp
import time
import re
import os
import shutil
from datetime import datetime

def clean_url(url):
    # 使用正则表达式匹配B站视频ID（BV号）
    match = re.search(r'(BV\w+)', url)
    if match:
        return f"https://www.bilibili.com/video/{match.group(1)}"
    return url  # 如果没有匹配到BV号，返回原始URL

def get_today_folder():
    folder = "today_download"
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

def organize_old_files():
    today = datetime.now().date()
    today_folder = get_today_folder()
    
    if not os.path.exists(today_folder):
        return
    
    for filename in os.listdir(today_folder):
        if filename.endswith('.mp3'):
            file_path = os.path.join(today_folder, filename)
            file_date = datetime.fromtimestamp(os.path.getctime(file_path)).date()
            if file_date < today:
                date_folder = os.path.join("downloads", file_date.strftime('%Y-%m-%d'))
                if not os.path.exists(date_folder):
                    os.makedirs(date_folder)
                shutil.move(file_path, os.path.join(date_folder, filename))

def download_video_as_mp3(url, output_path='audio.mp3', max_retries=3):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        # 添加登录信息，你需要替换为自己的账号密码
        'username': 'your_username',
        'password': 'your_password',
        # 降低质量要求
        'format': 'worstaudio/worst',
        # 添加重试和超时设置
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'no_warnings': True,
    }
    
    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return  # 如果成功，直接返回
        except Exception as e:
            print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
            else:
                raise  # 如果所有尝试都失败，抛出最后一个异常

def main():
    print("欢迎使用视频下载器！")
    organize_old_files()
    url = input("请输入哔哩哔哩视频链接：")
    cleaned_url = clean_url(url)
    print(f"清理后的URL: {cleaned_url}")
    
    today_folder = get_today_folder()
    default_filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    output_file = input(f"请输入保存的音频文件名（默认为 {default_filename}）：") or default_filename
    full_output_path = os.path.join(today_folder, output_file)

    try:
        download_video_as_mp3(cleaned_url, full_output_path)
        print(f"音频已成功下载并保存为 {full_output_path}")
    except Exception as e:
        print(f"下载失败：{str(e)}")

if __name__ == "__main__":
    main()

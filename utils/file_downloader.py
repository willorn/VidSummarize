import os
import time

import yt_dlp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def download_video_as_mp3(url, output_path, max_retries=3):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'username': os.getenv('BILIBILI_USERNAME'),
        'password': os.getenv('BILIBILI_PASSWORD'),
        'format': 'worstaudio/worst',
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'no_warnings': True,
    }

    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info['title']
                ydl.download([url])
            return title
        except Exception as e:
            print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
            else:
                raise


def download_video_as_wav(url, output_path, max_retries=3):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': output_path,
        'username': os.getenv('BILIBILI_USERNAME'),
        'password': os.getenv('BILIBILI_PASSWORD'),
        'format': 'bestaudio/best',  # 选择最佳音频质量
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'no_warnings': True,
    }

    for attempt in range(max_retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info['title']
                ydl.download([url])
            return title
        except Exception as e:
            print(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                print("等待5秒后重试...")
                time.sleep(5)
            else:
                raise

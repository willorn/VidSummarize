import os
import time
from typing import Dict, Any

import yt_dlp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_ydl_opts(output_path: str, audio_format: str) -> Dict[str, Any]:
    """
    获取下载选项
    """
    return {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': '192' if audio_format == 'mp3' else None,
        }],
        'outtmpl': output_path,
        'username': os.getenv('BILIBILI_USERNAME'),
        'password': os.getenv('BILIBILI_PASSWORD'),
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'no_warnings': True,
    }


def download_video(url: str, output_path: str, audio_format: str, max_retries: int = 3) -> str:
    ydl_opts = get_ydl_opts(output_path, audio_format)

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


def download_video_as_mp3(url: str, output_path: str, max_retries: int = 3) -> str:
    return download_video(url, output_path, 'mp3', max_retries)


def download_video_as_wav(url: str, output_path: str, max_retries: int = 3) -> str:
    return download_video(url, output_path, 'wav', max_retries)

import yt_dlp
import time
import re
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


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


def download_video_as_mp3(url, output_path='temp_audio', max_retries=3):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        # 从环境变量中获取账号和密码
        'username': os.getenv('BILIBILI_USERNAME'),
        'password': os.getenv('BILIBILI_PASSWORD'),
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


def get_next_file_number(folder):
    existing_files = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    numbers = [int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit()]
    return max(numbers) + 1 if numbers else 1


def main():
    print("欢迎使用视频下载器！")
    organize_old_files()
    url = input("请输入哔哩哔哩视频链接：")
    cleaned_url = clean_url(url)
    print(f"清理后的URL: {cleaned_url}")

    today_folder = get_today_folder()
    file_number = get_next_file_number(today_folder)

    try:
        temp_filename = 'temp_audio'
        title = download_video_as_mp3(cleaned_url, temp_filename)
        date_str = datetime.now().strftime('%Y%m%d')
        safe_title = re.sub(r'[\\/*?:"<>|]', '', title)  # 移除文件名中的非法字符
        new_filename = f"{file_number}.{safe_title}_{date_str}.mp3"
        full_output_path = os.path.join(today_folder, new_filename)
        
        # 查找并重命名临时文件
        temp_file = f"{temp_filename}.mp3"
        if os.path.exists(temp_file):
            os.rename(temp_file, full_output_path)
        else:
            print(f"警告：找不到临时文件 {temp_file}")
            # 尝试查找其他可能的临时文件名
            for file in os.listdir():
                if file.startswith(temp_filename) and file.endswith('.mp3'):
                    os.rename(file, full_output_path)
                    break
            else:
                raise FileNotFoundError(f"无法找到下载的音频文件")
        
        print(f"音频已成功下载并保存为 {full_output_path}")
    except Exception as e:
        print(f"下载失败：{str(e)}")


if __name__ == "__main__":
    main()

import os
import re
import shutil
from datetime import datetime


def ensure_dir_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_today_folder():
    file_date = datetime.now().date()
    date_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads", file_date.strftime('%Y-%m-%d'))
    # date_folder = os.path.join("../downloads", file_date.strftime('%Y-%m-%d'))
    ensure_dir_exists(date_folder)
    return date_folder


def organize_old_files():
    # today = datetime.now().date()
    #    today_folder = get_today_folder()
    #
    #    if not os.path.exists(today_folder):
    #        return
    #
    #    for filename in os.listdir(today_folder):
    #        if filename.endswith('.mp3'):
    #            file_path = os.path.join(today_folder, filename)
    #            file_date = datetime.fromtimestamp(os.path.getctime(file_path)).date()
    #            if file_date < today:
    #                date_folder = os.path.join("../downloads", file_date.strftime('%Y-%m-%d'))
    #                ensure_dir_exists(date_folder)
    #                shutil.move(file_path, os.path.join(date_folder, filename))
    a = 1 + 1


def get_next_file_number(folder):
    existing_files = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    numbers = [int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit()]
    return max(numbers) + 1 if numbers else 1


def get_temp_dir():
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads", "temp-dir")
    ensure_dir_exists(temp_dir)
    return temp_dir


def clean_filename(title):
    """
    移除文件名中的非法字符
    
    参数:
    title (str): 原始文件名或标题
    
    返回:
    str: 清理后的安全文件名
    """
    return re.sub(r'[\\/*?:"<>|]', '', title)


def move_temp_file_to_destination(temp_file_base, temp_dir, destination):
    """
    将临时文件移动到目标位置，处理临时文件名可能有变化的情况
    
    参数:
    temp_file_base (str): 临时文件的基本名称（不含扩展名）
    temp_dir (str): 临时文件所在目录
    destination (str): 目标文件的完整路径
    
    返回:
    bool: 是否成功移动文件
    
    抛出:
    FileNotFoundError: 如果找不到临时文件
    """
    # 尝试直接查找预期的临时文件
    temp_file = f"{temp_file_base}.wav"
    if os.path.exists(temp_file):
        shutil.move(temp_file, destination)
        return True

    # 查找其他可能的临时文件名
    for file in os.listdir(temp_dir):
        if file.startswith(os.path.basename(temp_file_base)) and file.endswith('.wav'):
            shutil.move(os.path.join(temp_dir, file), destination)
            return True

    raise FileNotFoundError(f"无法找到下载的音频文件")


def clean_temp_directory(temp_dir):
    """
    清理临时目录中的所有文件
    
    参数:
    temp_dir (str): 临时目录的路径
    """
    try:
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        print(f"清理临时目录时出错: {e}")

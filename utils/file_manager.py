import os
import shutil
from datetime import datetime


def get_today_folder():
    folder = "today_download"
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def get_temp_dir():
    temp_dir = "../temp-dir"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    return temp_dir


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
                date_folder = os.path.join("../downloads", file_date.strftime('%Y-%m-%d'))
                if not os.path.exists(date_folder):
                    os.makedirs(date_folder)
                shutil.move(file_path, os.path.join(date_folder, filename))


def get_next_file_number(folder):
    existing_files = [f for f in os.listdir(folder) if f.endswith('.mp3')]
    numbers = [int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit()]
    return max(numbers) + 1 if numbers else 1

import os
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

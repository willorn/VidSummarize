import ctypes
import re


def clean_url(url):
    """
    清理并标准化 Bilibili 视频 URL。

    此函数接受一个可能包含 Bilibili 视频 ID (BV号) 的 URL，
    并返回一个标准化的 Bilibili 视频 URL。

    参数:
    url (str): 输入的 URL 字符串

    返回:
    str: 标准化的 Bilibili 视频 URL，如果没有找到有效的 BV 号则返回原始 URL

    示例:
    >>> clean_url("https://www.bilibili.com/video/BV1xx411c7mD")
    "https://www.bilibili.com/video/BV1xx411c7mD"
    >>> clean_url("https://b23.tv/BV1xx411c7mD")
    "https://www.bilibili.com/video/BV1xx411c7mD"
    """
    match = re.search(r'(BV\w+)', url)
    if match:
        return f"https://www.bilibili.com/video/{match.group(1)}"
    return url


def empty_current_working_set():
    """
    清空当前工作集。

    此函数使用 Windows API 函数来清空当前进程的工作集。
    它首先获取当前进程的 ID，然后打开进程并获取句柄，
    接着使用 EmptyWorkingSet 函数清空工作集，最后关闭进程句柄。

    注意：此函数仅在 Windows 系统上有效。
    """
    # 使用 Windows API 函数 GetCurrentProcessId() 获取当前进程的ID。
    pid = ctypes.windll.kernel32.GetCurrentProcessId()
    # 使用 OpenProcess 函数打开进程，获取句柄, 0x1F0FFF 表示进程句柄的访问权限
    handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
    # 使用 EmptyWorkingSet 函数清空工作集
    ctypes.windll.psapi.EmptyWorkingSet(handle)
    # 使用 CloseHandle 函数关闭进程句柄
    ctypes.windll.kernel32.CloseHandle(handle)

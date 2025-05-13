import asyncio
import os
import sys
from pathlib import Path
from typing import List

import colorama
import typer
from rich.console import Console

from config import ClientConfig as Config
from utils.client_transcribe import transcribe_check, transcribe_send, transcribe_recv
from utils.client_ws import Cosmic

# 确保根目录位置正确，用相对路径加载模型
BASE_DIR = os.path.dirname(__file__)
os.chdir(BASE_DIR)  # 切换到当前目录

colorama.init(autoreset=True)  # 初始化 colorama, 确保终端能使用 ANSI 控制字符
console = Console()  # 创建一个 Console 对象


async def process_file(file: Path):
    """
    处理单个文件的函数
    根据文件类型选择适当的处理方法
    """
    # 对于其他文件（可能是音频或视频），进行转录
    await transcribe_check(file)
    await asyncio.gather(
        transcribe_send(file),
        transcribe_recv(file)
    )


async def process_files(files: List[Path]):
    """
    主要的异步函数，处理所有输入文件
    """
    console.print(f'【生成文本】Current Base Folder: [cyan underline]{os.getcwd()}')
    console.print(f'【生成文本】Server Address: [cyan underline]{Config.addr}:{Config.port}')

    for file in files:
        await process_file(file)

    # 关闭 websocket 连接
    if Cosmic.websocket:
        await Cosmic.websocket.close()


def run(files: List[Path]):
    """
    用 CapsWriter Server 转录音视频文件，生成 srt 字幕
    """
    try:
        asyncio.run(process_files(files))
    except KeyboardInterrupt:
        console.print('再见！')
        sys.exit()


if __name__ == "__main__":
    # 使用 typer 来处理命令行参数
    typer.run(run)

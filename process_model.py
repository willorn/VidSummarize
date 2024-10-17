import asyncio
import os
import sys
from multiprocessing import Process, Manager
from platform import system

import websockets

from config import ServerConfig as Config
from utils.common_utils import empty_current_working_set
from utils.server_model import check_model, init_recognizer
from utils.server_ws import Cosmic, console, ws_recv, ws_send

BASE_DIR = os.path.dirname(__file__)  # 获取当前文件的目录
os.chdir(BASE_DIR)  # 确保 os.getcwd() 位置正确，用相对路径加载模型


async def main_process():
    # 检查模型文件
    check_model()

    console.line(2)
    console.rule('[bold #d55252]Server For Speech to Text Base On ONNX');
    console.line()
    # console.print(f'项目地址：[cyan underline]https://github.com/willorn/VidSummarize', end='\n\n')
    # console.print(f'当前基文件夹：[cyan underline]{BASE_DIR}', end='\n\n')
    console.print(f'bind address: [cyan underline]{Config.addr}:{Config.port}', end='\n\n')

    # 跨进程列表，用于保存 socket 的 id，用于让识别进程查看连接是否中断
    Cosmic.sockets_id = Manager().list()

    # 负责识别的子进程
    recognize_process = Process(target=init_recognizer,
                                args=(Cosmic.queue_in,
                                      Cosmic.queue_out,
                                      Cosmic.sockets_id),
                                daemon=True)
    recognize_process.start()
    Cosmic.queue_out.get()
    console.rule('[green3]Start Server')
    console.line()

    # 清空物理内存工作集
    if system() == 'Windows':
        empty_current_working_set()

    # 负责接收客户端数据的 coroutine
    recv = websockets.serve(ws_recv,
                            Config.addr,
                            Config.port,
                            subprotocols=["binary"],
                            max_size=None)

    # 负责发送结果的 coroutine
    send = ws_send()
    await asyncio.gather(recv, send)


if __name__ == "__main__":
    try:
        asyncio.run(main_process())  # 运行主进程
    except KeyboardInterrupt:  # Ctrl-C 停止
        console.print('\nGoodbye!')
    except OSError as e:  # 端口占用
        console.print(f'Error: {e}', style='bright_red');
        console.input('...')
    except Exception as e:
        print(e)
    finally:
        Cosmic.queue_out.put(None)
        sys.exit(0)

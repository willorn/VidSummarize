import asyncio
import json
import time
from base64 import b64decode
from multiprocessing import Queue
from typing import Dict, List

import websockets
from rich.console import Console
from rich.console import RenderableType
from rich.status import Status as St
from rich.style import StyleType

from utils.server_classes import Task

console = Console(highlight=False)


class Status(St):
    """
    重写 rich 的 Status，让它知道自己是否正在播放
    """

    def __init__(
            self,
            status: RenderableType,
            *,
            spinner: str = "dots",
            spinner_style: StyleType = "status.spinner",
            speed: float = 1.0,
            refresh_per_second: float = 12.5
    ):
        super().__init__(
            status,
            console=None,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
            refresh_per_second=refresh_per_second,
        )
        self.is_running = False

    def start(self) -> None:
        if not self.is_running:
            self.is_running = True
            super().start()

    def stop(self) -> None:
        if self.is_running:
            self.is_running = False
            super().stop()


status_mic = Status('正在接收音频文件', spinner='point')


class Cosmic:
    """
    Cosmic 类用于管理 WebSocket 连接和消息队列。

    这个类的主要作用是:
    1. 管理 WebSocket 连接：存储和跟踪活动的 WebSocket 连接。
    2. 处理消息队列：管理输入和输出消息队列，用于异步通信。
    3. 提供接口：为其他部分的代码提供接口，以便与 WebSocket 客户端进行交互。

    属性:
        sockets (Dict[str, websockets.WebSocketClientProtocol]): 存储 WebSocket 连接的字典。
        sockets_id (List): 存储 WebSocket 连接 ID 的列表。
        queue_in (Queue): 输入消息队列，用于接收来自客户端的消息。
        queue_out (Queue): 输出消息队列，用于发送消息给客户端。
    """
    sockets: Dict[str, websockets.WebSocketClientProtocol] = {}
    sockets_id: List
    queue_in = Queue()
    queue_out = Queue()


# 主要处理 web socket 相关的东西


class Cache:
    def __init__(self):
        self.chunks = bytearray()
        self.offset = 0
        self.frame_num = 0


async def message_handler(websocket, message, cache: Cache):
    queue_in = Cosmic.queue_in

    global status_mic
    source = message['source']
    is_final = message['is_final']
    is_start = not cache.chunks

    task_id = message['task_id']
    socket_id = str(websocket.id)

    seg_duration = message['seg_duration']
    seg_overlap = message['seg_overlap']

    cache.chunks.extend(b64decode(message['data']))
    cache.frame_num += len(cache.chunks)

    if not is_final:
        if source == 'mic':
            status_mic.start()
        elif source == 'file' and is_start:
            console.print('正在接收音频文件...')

        chunk_size = int(4 * 16000 * (seg_duration + seg_overlap))
        while len(cache.chunks) >= chunk_size:
            data = bytes(cache.chunks[:chunk_size])
            del cache.chunks[:int(4 * 16000 * seg_duration)]
            task = Task(source=source,
                        data=data, offset=cache.offset,
                        task_id=task_id, socket_id=socket_id,
                        overlap=seg_overlap, is_final=False,
                        time_start=message['time_start'],
                        time_submit=time.time())
            cache.offset += seg_duration
            queue_in.put(task)

    else:
        if source == 'mic':
            status_mic.stop()
        elif source == 'file':
            print(f'音频文件接收完毕，时长 {cache.frame_num / 16000 / 4:.2f}s')

        task = Task(source=source,
                    data=bytes(cache.chunks), offset=cache.offset,
                    task_id=task_id, socket_id=socket_id,
                    overlap=seg_overlap, is_final=True,
                    time_start=message['time_start'],
                    time_submit=time.time())
        queue_in.put(task)

        cache.chunks.clear()
        cache.offset = 0
        cache.frame_num = 0


async def ws_recv(websocket):
    global status_mic

    sockets = Cosmic.sockets
    sockets_id = Cosmic.sockets_id
    sockets[str(websocket.id)] = websocket
    sockets_id.append(str(websocket.id))
    console.print(f'接客了：{websocket}\n', style='yellow')

    cache = Cache()

    try:
        async for message in websocket:
            message = json.loads(message)
            await message_handler(websocket, message, cache)

    except websockets.ConnectionClosed:
        console.print("ConnectionClosed...")
    except websockets.InvalidState:
        console.print("InvalidState...")
    except Exception as e:
        console.print(f"Exception: {e}")
    finally:
        status_mic.stop()
        status_mic.on = False
        sockets.pop(str(websocket.id))
        sockets_id.remove(str(websocket.id))


async def ws_send():
    queue_out, sockets = Cosmic.queue_out, Cosmic.sockets

    while True:
        try:
            result = await asyncio.to_thread(queue_out.get)

            if result is None:
                return

            message = {
                'task_id': result.task_id,
                'duration': result.duration,
                'time_start': result.time_start,
                'time_submit': result.time_submit,
                'time_complete': result.time_complete,
                'tokens': result.tokens,
                'timestamps': result.timestamps,
                'text': result.text,
                'is_final': result.is_final,
            }

            websocket = next((ws for ws in sockets.values() if str(ws.id) == result.socket_id), None)
            if not websocket:
                continue

            await websocket.send(json.dumps(message))

            if result.source == 'mic':
                console.print(f'识别结果：\n    [green]{result.text}')
            elif result.source == 'file':
                console.print(f'    转录进度：{result.duration:.2f}s', end='\r')
                if result.is_final:
                    console.print('\n    [green]转录完成')

        except Exception as e:
            console.print(f'错误：{e}', style='bold red')


async def start_server(host, port):
    server = await websockets.serve(
        ws_recv,
        host,
        port,
        subprotocols=['binary'],
        max_size=None
    )
    await server.wait_closed()

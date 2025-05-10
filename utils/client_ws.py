from asyncio import Queue, AbstractEventLoop
from typing import List, Union

import sounddevice as sd
import websockets
from rich.console import Console
from rich.theme import Theme

from config import ClientConfig as Config

my_theme = Theme({'markdown.code': 'cyan', 'markdown.item.number': 'yellow'})
console = Console(highlight=False, soft_wrap=False, theme=my_theme)


# from utils.client_cosmic import Cosmic

class Cosmic:
    """
    用一个 class 存储需要跨模块访问的变量值，命名为 Cosmic
    """
    on = False
    queue_in: Queue
    queue_out: Queue
    loop: Union[None, AbstractEventLoop] = None
    websocket: websockets.WebSocketClientProtocol = None
    audio_files = {}
    stream: Union[None, sd.InputStream] = None
    kwd_list: List[str] = []


class Handler:
    def __enter__(self):
        ...

    def __exit__(self, exc_type, e, exc_tb):
        if e is None:
            return True
        if isinstance(e, ConnectionRefusedError):
            return True
        elif isinstance(e, TimeoutError):
            return True
        elif isinstance(e, Exception):
            return True
        else:
            print(e)


async def check_websocket() -> bool:
    if Cosmic.websocket and not Cosmic.websocket.closed:
        return True
    for _ in range(3):
        with Handler():
            Cosmic.websocket = await websockets.connect(
                f"ws://{Config.addr}:{Config.port}",
                max_size=None,
                subprotocols=['binary']
            )
            return True
    else:
        return False

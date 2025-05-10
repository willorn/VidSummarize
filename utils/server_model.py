import concurrent.futures
import signal
import time
from multiprocessing import Queue
from pathlib import Path
from platform import system
from queue import Empty
from typing import List

import sherpa_onnx
from funasr_onnx import CT_Transformer

from config import ServerConfig as Config, ParaformerArgs, ModelPaths
from utils.common_utils import empty_current_working_set
from utils.server_model_test import recognize
from utils.server_ws import console


def get_missing_models() -> List[Path]:
    return [
        Path(path) for key, path in vars(ModelPaths).items()
        if not key.startswith('_') and not Path(path).exists()
    ]


def format_error_message(missing_models: List[Path]) -> str:
    return f'''
未能找到以下模型文件：

{chr(10).join(f"- {path}" for path in missing_models)}

请下载 `paraformer-offline-zh` 和 `punc_ct-transformer_zh-cn` 模型，
并放置到：{ModelPaths.model_dir}
    '''


def check_model():
    missing_models = get_missing_models()

    if missing_models:
        console.print(format_error_message(missing_models), style='bright_red')
        input('Press Enter to exit')
        raise SystemExit("Missing model files")


def disable_jieba_debug():
    # 关闭 jieba 的 debug
    import jieba
    import logging
    jieba.setLogLevel(logging.INFO)


def load_speech_model() -> sherpa_onnx.OfflineRecognizer:
    console.print('[yellow]载入语音模型中...', end='\r')
    recognizer = sherpa_onnx.OfflineRecognizer.from_paraformer(
        **{k: v for k, v in vars(ParaformerArgs).items() if not k.startswith('_')}
    )
    console.print('[green]语音模型载入完成', end='\n')
    return recognizer


def load_punctuation_model() -> CT_Transformer | None:
    if not Config.format_punc:
        return None
    console.print('[yellow]载入标点模型中...', end='\r')
    punc_model = CT_Transformer(ModelPaths.punc_model_dir, quantize=True)
    console.print('[green]标点模型载入完成', end='\n')
    return punc_model


def process_tasks(queue_in: Queue, queue_out: Queue, sockets_id: List[int],
                  recognizer: sherpa_onnx.OfflineRecognizer):
    while True:
        try:
            task = queue_in.get(timeout=1)
            if task.socket_id not in sockets_id:
                continue
            result = recognize(recognizer, task)
            queue_out.put(result)
        except Empty:
            continue


def load_models():
    console.print('[yellow]正在加载模型...', end='\r')
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        speech_future = executor.submit(load_speech_model)
        # punc_future = executor.submit(load_punctuation_model)

        recognizer = speech_future.result()
        # punc_model = punc_future.result()

    total_time = time.time() - start_time
    console.print(f'[green]模型加载完成，总耗时 {total_time:.2f}s', end='\n\n')
    return recognizer


def init_recognizer(queue_in: Queue, queue_out: Queue, sockets_id: List[int]):
    # 捕获 Ctrl-C 信号，退出程序
    signal.signal(signal.SIGINT, lambda signum, frame: exit())

    # 载入模块
    with console.status("loading modules...", spinner="bouncingBall", spinner_style="yellow"):
        disable_jieba_debug()

    # 载入模型
    recognizer = load_models()

    # 释放内存
    if system() == 'Windows':
        empty_current_working_set()

    queue_out.put(True)  # 通知主进程加载完了

    # 处理任务
    process_tasks(queue_in, queue_out, sockets_id, recognizer)

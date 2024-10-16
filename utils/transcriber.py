import asyncio
from pathlib import Path
from sherpa_onnx import AsrConfig, OfflineRecognizer
from funasr_onnx import CT_Transformer

# 模型路径
PARAFORMER_MODEL = "path/to/paraformer-offline-zh/model.int8.onnx"
PARAFORMER_TOKENS = "path/to/paraformer-offline-zh/tokens.txt"
PUNCTUATION_MODEL = "path/to/punc_ct-transformer_cn-en"


def init_recognizer():
    return OfflineRecognizer(
        AsrConfig(
            paraformer=PARAFORMER_MODEL,
            tokens=PARAFORMER_TOKENS,
        )
    )


def init_punctuation_model():
    return CT_Transformer(PUNCTUATION_MODEL, quantize=True)


async def preprocess_audio(file_path):
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", str(file_path),
        "-f", "f32le",
        "-ac", "1",
        "-ar", "16000",
        "-"
    ]
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    audio_data, _ = await process.communicate()
    return audio_data


def recognize_audio(recognizer, audio_data, sample_rate=16000):
    stream = recognizer.create_stream()
    stream.accept_waveform(sample_rate, audio_data)
    recognizer.decode_stream(stream)
    text = stream.result.text
    timestamps = stream.result.timestamps
    return text, timestamps


def add_punctuation(text, punc_model):
    return punc_model(text)[0]


def generate_timestamped_text(text, timestamps):
    result = []
    for token, time in zip(text.split(), timestamps):
        result.append(f"[{time:.2f}] {token}")
    return "\n".join(result)


async def process_audio_file(file_path):
    recognizer = init_recognizer()
    punc_model = init_punctuation_model()

    audio_data = await preprocess_audio(file_path)
    text, timestamps = recognize_audio(recognizer, audio_data)
    text_with_punctuation = add_punctuation(text, punc_model)
    final_text = generate_timestamped_text(text_with_punctuation, timestamps)

    return final_text


def transcribe_audio(input_path, output_path):
    audio_file = Path(input_path)
    final_text = asyncio.run(process_audio_file(audio_file))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)

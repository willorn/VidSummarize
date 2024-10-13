import whisper
import os
import subprocess


def get_ffmpeg_path():
    # 假设 FFmpeg 在项目根目录的 'ffmpeg' 文件夹中
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'ffmpeg.exe')


def print_ffmpeg_version():
    ffmpeg_path = get_ffmpeg_path()
    try:
        result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
        print("使用的 FFmpeg 版本:")
        print(result.stdout.split('\n')[0])  # 只打印第一行，通常包含版本信息
    except Exception as e:
        print(f"无法获取 FFmpeg 版本信息: {e}")


def transcribe_audio(audio_path, output_path):
    print_ffmpeg_version()

    print("正在加载 Whisper 模型...")
    model = whisper.load_model("medium")

    print(f"开始转录音频文件: {audio_path}")
    result = model.transcribe(audio_path)

    print(f"转录完成，正在保存到文件: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result["text"])

    print("转录文本已保存")

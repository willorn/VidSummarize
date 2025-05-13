#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试AI摘要生成器
"""

import os
from pathlib import Path

from utils.ai_summarizer import summarize_video

# 测试数据
TEST_DATA = """
0 大家好，今天我将介绍如何使用Python处理视频
12 首先，我们需要安装必要的库
20 我们可以用FFmpeg来转换视频格式
35 接下来，让我们编写代码提取视频帧
50 最后，我们将处理音频并生成字幕
"""


def main():
    print("AI摘要生成器测试程序")
    print("-" * 40)

    # 确保存在.env文件
    if not os.path.exists("../../.env"):
        print("警告：.env文件不存在。如果您还没有创建，请复制.env.example为.env")

    # 创建临时测试文件
    test_file = Path("test_summary_input.txt")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(TEST_DATA)
    print(f"已创建测试输入文件：{test_file}")

    # 测试URL
    test_url = "https://www.bilibili.com/video/BV1xx411c7mD"

    try:
        print(f"\n正在使用URL '{test_url}'生成摘要...")
        result = summarize_video(test_file, test_url)

        # 保存结果
        output_file = Path("test_summary_output.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)

        print(f"\n摘要生成成功！结果已保存到：{output_file}\n")
        print("摘要内容预览：")
        print("-" * 40)
        # 只显示前10行或全部（如果少于10行）
        preview_lines = result.splitlines()[:10]
        for line in preview_lines:
            print(line)

        if len(result.splitlines()) > 10:
            print("...")
        print("-" * 40)

    except Exception as e:
        print(f"生成摘要时出错：{str(e)}")
    finally:
        # 清理测试文件（可选）
        # if test_file.exists():
        #     test_file.unlink()
        #     print(f"已删除测试文件：{test_file}")
        pass

    print("\n测试完成！")


if __name__ == "__main__":
    main()

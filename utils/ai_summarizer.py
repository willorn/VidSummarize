import json
import os
import re
from pathlib import Path
from typing import Optional, Union

import requests

# 导入dotenv用于加载.env文件
try:
    from dotenv import load_dotenv

    # 尝试加载.env文件
    load_dotenv()
    ENV_LOADED = True
except ImportError:
    print("警告: python-dotenv 未安装，将不会加载.env文件")
    ENV_LOADED = False


# 适配不同的API
class AISummarizer:
    """
    使用AI生成视频总结和跳转链接的类
    """

    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化AI总结器
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            api_base: API基础URL，如果为None则使用默认值
        """
        # 从参数或环境变量获取API密钥和基础URL
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")

        # 打印当前配置信息（隐藏API密钥的大部分内容）
        if self.api_key:
            masked_key = self.api_key[:5] + "*" * 5 + self.api_key[-5:] if len(self.api_key) > 10 else "*" * len(
                self.api_key)
            print(f"使用API密钥: {masked_key}")
            print(f"使用API基础URL: {self.api_base}")
        else:
            print("警告: 没有设置API密钥，请设置OPENAI_API_KEY环境变量或在.env文件中配置")

    def generate_summary(self, main_txt_file: Union[str, Path], original_url: str) -> str:
        """
        生成视频总结和跳转链接
        
        Args:
            main_txt_file: 包含时间戳和文本内容的文件路径
            original_url: 原始视频URL
            
        Returns:
            生成的markdown格式摘要
        """
        try:
            # 读取输入文件
            with open(main_txt_file, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                return "错误: 输入文件内容为空"

            # 构建prompt
            prompt = self._build_prompt(content, original_url)

            # 调用API
            response = self._call_api(prompt)

            if response:
                # 保存生成的内容到与输入文件同名但后缀为.merge.txt的文件
                output_file = str(main_txt_file).replace('.main.txt', '.final.md')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response)
                print(f"已生成摘要并保存到: {output_file}")
                return response
            else:
                return "API调用失败，未能生成摘要"

        except Exception as e:
            print(f"生成摘要时出错: {str(e)}")
            return f"错误: {str(e)}"

    def _build_prompt(self, content: str, original_url: str) -> str:
        """构建发送给AI的prompt"""
        # 从URL中提取BV号
        bv_match = re.search(r'(BV\w+)', original_url)
        bv_id = bv_match.group(1) if bv_match else ""

        return f"""你现在是一个视频总结小助手，能够帮我提供一个文档作为视频总结和快速跳转

视频链接: {original_url}
BV号: {bv_id}

## 输入
包含时间戳（秒）以及内容的文本信息

## 输出
直接输出markdown文档内容，不要包含提示信息
1、视频大总结
2、视频小总结：哔哩哔哩视频跳转链接的列表（跳转的链接格式如下：https://www.bilibili.com/video/{bv_id}?t=1）
以下是格式：
||||
|----|----|----|
|时间线|内容在整个视频中的占比|视频内容|

3、这个视频比较适合那些人看，有什么特色


以下是我的输入，
{content}
"""

    def _call_api(self, prompt: str) -> Optional[str]:
        """
        调用AI API
        
        Args:
            prompt: 要发送的提示文本
            
        Returns:
            API返回的文本内容，失败时返回None
        """
        if not self.api_key:
            print("错误: 未设置API密钥")
            return None

        try:
            # 打印当前使用的API端点详细信息，便于调试
            print(f"将请求发送到: {self.api_base}")

            # FastGPT的API调用方式与OpenAI不同
            if "ziki.top" in self.api_base:
                print("\n使用FastGPT API...")

                # 尝试不同的FastGPT API调用方式

                # 方式1: 将API密钥放在请求头中
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                # 方式1的请求体
                payload1 = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的视频总结助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }

                # 方式2: 使用apiKey参数
                payload2 = {
                    "apiKey": self.api_key,
                    "prompt": prompt,
                    "temperature": 0.7
                }

                # 自动尝试不同的调用方式
                api_url = self.api_base.rstrip('/')
                success = False
                response = None

                # 不同的API调用方式
                api_methods = [
                    {
                        "name": "Authorization header + OpenAI 格式",
                        "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                        "payload": payload1,
                        "endpoint": f"{api_url}/v1/chat/completions"
                    },
                    {
                        "name": "Authorization header + 基础格式",
                        "headers": {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
                        "payload": payload1,
                        "endpoint": api_url
                    },
                    {
                        "name": "apiKey参数",
                        "headers": {"Content-Type": "application/json"},
                        "payload": payload2,
                        "endpoint": api_url
                    },
                    {
                        "name": "key参数",
                        "headers": {"Content-Type": "application/json"},
                        "payload": {"key": self.api_key, "prompt": prompt},
                        "endpoint": api_url
                    },
                    {
                        "name": "API密钥作为URL参数",
                        "headers": {"Content-Type": "application/json"},
                        "payload": {"messages": [{"role": "user", "content": prompt}]},
                        "endpoint": f"{api_url}?key={self.api_key}"
                    }
                ]

                # 尝试每种方法
                for method in api_methods:
                    try:
                        print(f"\n\n尝试方法: {method['name']}")
                        print(f"\n请求URL: {method['endpoint']}")
                        print(f"\n请求头: {method['headers']}")
                        # 支持中文输出且限制输出长度
                        payload_preview = json.dumps(method['payload'], ensure_ascii=False)[:100]
                        print(f"\n请求体: {payload_preview}{'...' if len(payload_preview) == 100 else ''}")

                        response = requests.post(
                            method['endpoint'],
                            headers=method['headers'],
                            json=method['payload'],
                            timeout=30  # 添加超时设置
                        )

                        print(f"\n状态码: {response.status_code}")

                        if response.status_code == 200:
                            print("\n该方法请求成功!")
                            success = True
                            break
                        else:
                            print(f"\n返回内容: {response.text[:200]}")
                            if '402' in response.text or '403' in response.text:
                                print("授权错误，尝试下一种方法")
                            else:
                                print("非授权错误，可能不需要尝试其他方法")
                                break
                    except Exception as e:
                        print(f"\n该方法异常: {str(e)}")
                        continue

                if not success and response is None:
                    print("\n所有API调用方法都失败了")
                    return "无法连接到AI API，请检查网络和API密钥"

                if not success:
                    print("\n所有方法均返回错误状态码")

                # 处理响应
                print(f"\n响应状态码: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"\n响应结果类型: {type(result)}")
                        print(f"\n响应结果键: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

                        # 尝试不同的响应格式
                        if isinstance(result, dict):
                            if "text" in result:
                                return result["text"]
                            elif "choices" in result and len(result["choices"]) > 0:
                                if isinstance(result["choices"][0], dict) and "text" in result["choices"][0]:
                                    return result["choices"][0]["text"]
                                elif isinstance(result["choices"][0], dict) and "message" in result["choices"][0]:
                                    return result["choices"][0]["message"]["content"]
                            elif "data" in result and isinstance(result["data"], str):
                                return result["data"]
                            # 如果是纯文本返回
                        elif isinstance(result, str):
                            return result

                        # 输出完整响应作为调试
                        print(f"\n完整响应: {json.dumps(result, ensure_ascii=False)}")
                        return str(result)  # 返回字符串形式的完整响应
                    except Exception as e:
                        print(f"\n解析FastGPT响应时出错: {str(e)}")
                        return response.text  # 返回原始文本
            else:
                # 标准OpenAI API格式
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }

                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的视频总结助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }

                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]

            # 处理错误情况
            print(f"API调用失败，状态码: {response.status_code}")
            print(f"请求URL: {self.api_base}")
            print(f"返回内容: {response.text}")
            return None

        except Exception as e:
            print(f"API调用出错: {str(e)}")
            return None


# 简单使用示例
def summarize_video(main_txt_file: Union[str, Path], original_url: str, api_key: Optional[str] = None,
                    api_base: Optional[str] = None) -> str:
    """
    生成视频总结和跳转链接的简便函数
    
    Args:
        main_txt_file: 包含时间戳和文本内容的文件路径
        original_url: 原始视频URL
        api_key: 可选的API密钥
        api_base: 可选的API基础URL
        
    Returns:
        生成的markdown格式摘要
    """
    summarizer = AISummarizer(api_key=api_key, api_base=api_base)
    return summarizer.generate_summary(main_txt_file, original_url)

# VidSummarize
The project leverages local GPU resources to download and convert video audio to text, summarize it using a large model, and display the results on a webpage.

### Task List

1. **视频下载 (Bilibili / YouTube)** ——Done 2024年10月14日00:18:06
   - 实现视频下载功能，支持将哔哩哔哩或 YouTube 视频直接下载为 MP3 格式。
   - 考虑使用工具如 `youtube-dl` 或 `yt-dlp`。

2. **MP3 转 TXT（带时间戳）**——in Develop
   - 开发或整合大模型，将 MP3 音频文件转为带时间戳的 TXT 文本。
   - 确保时间戳信息保留，便于后续总结时定位视频内容。
   - 目前能跑通，但是时间长的离谱，10分钟的视频竟然需要1H20min才能完成转换，性价比太低。等待优化 2024年10月14日01:10:23

3. **文本总结 (本地大模型)**
   - 使用本地 GPU 资源，加载并运行大模型对生成的 TXT 文本进行总结。
   - **子任务：**
     1. **按视频主题总结**：生成不同主题的摘要。
     2. **网络检索相关信息**：扩展视频内容，通过网络搜索相关的上下文信息。

4. **用户界面展示**
   - 构建一个简单的网页，展示总结的内容。
   - 界面应包含视频各主题的摘要，时间戳，以及通过网络检索获得的附加信息。


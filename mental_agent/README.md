# Coze聊天机器人API服务

基于Coze API的心理健康聊天机器人服务，提供智能对话、情绪分析和文本转语音功能。

## 🌟 功能特性

### 核心功能
- **🤖 智能对话**: 基于Coze API的自然语言理解和生成
- **🧠 情绪分析**: 智能识别文本中的情绪标签，支持置信度评估
- **🗣️ 文本转语音**: 将文本转换为高质量音频，支持多种音色和情感
- **💬 多轮对话**: 自动维护会话上下文，支持连续对话
- **📊 会话管理**: 提供会话查询、清除等管理功能
- **🔄 流式响应**: 支持Server-Sent Events (SSE) 实时流式响应

### 技术特性
- **⚡ 高性能**: 基于FastAPI的异步处理架构
- **📱 RESTful API**: 标准化REST接口设计
- **🔐 安全性**: 完善的错误处理和输入验证
- **📖 文档完整**: 自动生成Swagger/OpenAPI文档

## 🚀 快速开始

### 环境要求
- Python 3.8+
- 网络连接（用于Coze API）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的Coze API配置：
```env
# Coze API配置
COZE_BOT_ID=your_bot_id_here
COZE_USER_ID=your_user_id_here
COZE_API_TOKEN=your_token_here
```

### 运行服务
```bash
# 启动API服务器
python api_server.py

# 或使用演示脚本
python run_server_and_demo.py
```

服务启动后，访问 http://localhost:6001/docs 查看完整API文档。

## 📋 API接口示例

### 基础聊天接口

#### 同步聊天
```python
import requests

response = requests.post(
    "http://localhost:6001/chat",
    json={
        "user_id": "user123",
        "message": "我今天感觉很焦虑",
        "session_id": "session123"
    }
)

result = response.json()
print(f"回复: {result['response']}")
```

#### 流式聊天
```python
import requests
import json

response = requests.post(
    "http://localhost:6001/chat/stream",
    json={
        "user_id": "user123", 
        "message": "我今天感觉很焦虑",
        "session_id": "session123"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        print(data['content'], end='', flush=True)
```

### 情绪分析接口
```python
import requests

response = requests.post(
    "http://localhost:6001/analyze-emotion",
    json={
        "user_id": "user123",
        "text": "我今天很开心，但也有点担心",
        "session_id": "session123"
    }
)

result = response.json()
print(f"情绪标签: {result['emotion_tags']}")
print(f"置信度: {result['confidence_scores']}")
```

### 文本转语音接口
```python
import requests

response = requests.post(
    "http://localhost:6001/text-to-speech",
    json={
        "text": "你好，今天过得怎么样？",
        "voice_id": "default",
        "emotion": "happy"
    }
)

with open("output.mp3", "wb") as f:
    f.write(response.content)
```

### 会话管理
```python
# 获取会话信息
response = requests.get("http://localhost:6001/session/session123")
session_info = response.json()

# 清除会话
response = requests.delete("http://localhost:6001/session/session123")
print(f"清除结果: {response.json()}")
```

## 📁 项目结构

```
mental/
├── api_server.py              # Web API服务器
├── coze_api_client.py         # Coze API客户端
├── coze_emotiontag.py         # 情绪分析模块
├── coze_tts_client.py         # 文本转语音模块
├── run_server_and_demo.py     # 演示脚本
├── config.py                  # 配置文件
├── requirements.txt           # 依赖包
├── .env.example               # 环境变量模板
├── API_DOCUMENTATION_v1.0.md  # 完整API文档
├── README.md                  # 项目文档
└── logs/                      # 日志目录
```

## ⚙️ 配置说明

### 环境变量配置
复制 `.env.example` 为 `.env` 并配置：
```bash
# Coze API配置
COZE_API_TOKEN=your_api_token
COZE_BOT_ID=your_bot_id
COZE_USER_ID=your_user_id

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=6001
DEBUG=false
```

## 📞 支持

如有问题，请：
1. 查看日志文件获取错误信息
2. 检查配置文件是否正确
3. 查看 `API_DOCUMENTATION_v1.0.md` 获取详细API文档

## 📄 许可证

MIT License

## 🙏 致谢

- Coze API提供强大的AI能力
- 开源社区提供的优秀库和工具

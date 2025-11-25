# Coze聊天机器人API接口文档 v1.3.0

## 概述

基于Coze API的心理健康聊天机器人API服务，提供同步和流式两种聊天模式，支持会话管理、上下文维护和conversation_id续传功能，新增情绪标签识别和文本转语音功能。

### 核心特性

- 🤖 **智能对话**: 基于Coze API的自然语言理解和生成
- 🔄 **流式输出**: 支持Server-Sent Events (SSE) 实时流式响应
- 💬 **多轮对话**: 自动维护会话上下文，支持连续对话
- 🔗 **会话续传**: 支持conversation_id续传现有会话
- 🎯 **会话绑定**: 自动管理session_id与conversation_id的映射关系
- 📊 **会话管理**: 提供会话查询、清除等管理功能
- 🛡️ **错误处理**: 完善的异常处理和日志记录
- 📖 **自动文档**: Swagger/OpenAPI自动生成接口文档
- 🧠 **情绪分析**: 智能识别文本中的情绪标签，支持置信度评估
- 🗣️ **文本转语音**: 将文本转换为高质量的音频文件，支持多种音色和情感设置

### 基础信息

- **版本**: 1.3.0
- **基础URL**: `http://localhost:6001`
- **API文档**: `http://localhost:6001/docs`
- **协议**: HTTP/1.1 + SSE
- **数据格式**: JSON

### 核心功能

- 🤖 **智能对话**: 基于Coze API的自然语言理解和生成
- 🔄 **流式输出**: 支持Server-Sent Events (SSE) 实时流式响应
- 💬 **多轮对话**: 自动维护会话上下文，支持连续对话
- 🔗 **会话续传**: 支持conversation_id续传现有会话
- 🎯 **会话绑定**: 自动管理session_id与conversation_id的映射关系
- 📊 **会话管理**: 提供会话查询、清除等管理功能
- 🛡️ **错误处理**: 完善的异常处理和日志记录
- 📖 **自动文档**: Swagger/OpenAPI自动生成接口文档
- 🧠 **情绪分析**: 智能识别文本中的情绪标签，支持置信度评估
- 🗣️ **文本转语音**: 将文本转换为高质量的音频文件，支持多种音色和情感设置

---

## 快速开始

### 1. 环境准备

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# Coze API配置
COZE_API_TOKEN=your_api_token_here
COZE_BOT_ID=your_bot_id_here
COZE_USER_ID=default_user
COZE_BASE_URL=https://api.coze.cn/v3

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=6001
DEBUG=false
```

### 3. 启动服务

```bash
# 启动API服务器
python api_server.py

# 或使用uvicorn直接启动
uvicorn api_server:app --host 0.0.0.0 --port 6001 --reload
```

### 4. 健康检查

```bash
curl http://localhost:6001/health   
```

---

## API接口详解

### 1. 系统状态接口

#### 1.1 健康检查

- **接口**: `GET /health`
- **描述**: 检查服务运行状态
- **响应示例**:

```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00",
    "coze_client_status": "initialized"
}
```

#### 1.2 根路径

- **接口**: `GET /`
- **描述**: 服务基本信息
- **响应示例**:

```json
{
    "message": "Coze聊天机器人API服务正在运行",
    "version": "1.3.0",
    "status": "healthy",
    "docs": "/docs",
    "features": {
        "chat_sync": "同步聊天功能",
        "chat_stream": "流式聊天功能",
        "emotion_analysis": "情绪标签识别功能",
        "text_to_speech": "文本转语音功能",
        "session_management": "会话管理功能"
    }
}
```

---

### 2. 聊天功能接口

#### 2.1 同步聊天

- **接口**: `POST /chat`
- **描述**: 发送聊天消息并获取完整回复（阻塞模式）
- **请求头**:

```
Content-Type: application/json
```

- **请求体**:

```json
{
    "user_id": "user123",           // 可选，用户ID
    "message": "我最近工作压力很大",   // 必填，消息内容
    "session_id": "demo_session_1"   // 可选，会话ID
}
```

- **响应示例**:

```json
{
    "response": "我理解您的工作压力。以下是一些缓解压力的建议...",
    "session_id": "demo_session_1",
    "message_id": "msg_abc123def456",
    "timestamp": "2024-01-15T10:30:15.123456",
    "conversation_id": "conv_789xyz"
}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "你好，我想聊聊最近的心情",
       "session_id": "my_session"
     }'
```

#### 2.2 流式聊天

- **接口**: `POST /chat/stream`
- **描述**: 发送聊天消息并获取流式回复（实时输出）
- **请求体**: 与同步聊天相同
- **响应类型**: `text/event-stream` (SSE)

**流式响应格式**:

```text
data: {"type": "chunk", "data": {"content": "我理解您的", "chunk_index": 0, "total_chunks": 5}}
data: {"type": "chunk", "data": {"content": "感受。让我们", "chunk_index": 1, "total_chunks": 5}}
data: {"type": "chunk", "data": {"content": "一起探讨", "chunk_index": 2, "total_chunks": 5}}
data: {"type": "complete", "data": {"total_chunks": 3, "full_content": "我理解您的感受。together..."}}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/chat/stream" \
     -H "Content-Type: application/json" \
     -d '{"message": "能给我一些缓解压力的建议吗？"}' \
     --no-buffer
```

---

### 3. 情绪分析接口

#### 3.1 情绪标签识别

- **接口**: `POST /analyze-emotion`
- **描述**: 分析文本中的情绪标签，基于Coze API进行智能情绪识别
- **请求头**:

```
Content-Type: application/json
```

- **请求体**:

```json
{
    "user_id": "user123",           // 可选，用户ID
    "text": "我最近工作压力很大，感觉很焦虑",   // 必填，要分析的文本内容
    "session_id": "demo_session_1"  // 可选，会话ID
}
```

- **响应示例**:

```json
{
    "emotion_tags": ["焦虑", "压力", "疲惫"],
    "confidence_scores": [0.85, 0.72, 0.65],
    "analysis_result": "用户表达了工作压力相关的负面情绪，建议提供缓解压力的建议和心理支持",
    "emotion_intensity": "中等",
    "session_id": "demo_session_1",
    "timestamp": "2024-01-20T14:30:00.123456"
}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/analyze-emotion" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "我今天心情很好，工作效率很高",
       "session_id": "my_session"
     }'
```

- **响应字段说明**:
  - `emotion_tags`: 识别的情绪标签数组
  - `confidence_scores`: 对应的置信度分数（0-1之间）
  - `analysis_result`: 情绪分析结果描述
  - `emotion_intensity`: 情绪强度（低/中等/高）
  - `session_id`: 会话ID
  - `timestamp`: 分析时间戳

### 4. 文本转语音接口

#### 4.1 文本转语音

- **接口**: `POST /text-to-speech`
- **描述**: 将文本转换为高质量的MP3音频文件
- **请求头**:

```
Content-Type: application/json
```

- **请求体**:

```json
{
    "input": "你好，我是你的人工智能助手",   // 必填，合成语音的文本（UTF-8编码，≤1024字节）
    "voice_id": "7426725529681657907"     // 可选，音色ID（需通过音色列表API获取可用值）
    "emotion": "neutral",                 // 可选，情感类型（happy/sad/angry/surprised/fear/hate/excited/coldness/neutral）
    "emotion_scale": 3.0                  // 可选，情感强度（1.0~5.0，数值越高情感越强烈）
}
```

- **响应类型**: `audio/mpeg`（MP3音频流）

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/text-to-speech" \
     -H "Content-Type: application/json" \
     -d '{"input": "你好，我是你的人工智能助手", "voice_id": "7426725529681657907"}' \
     --output output.mp3
```

- **响应示例**:

```json
{
    "task_id": "tts_task_abc123def456",
    "voice_id": "7426725529681657907",
    "text_length": 20,
    "audio_format": "mp3",
    "timestamp": "2024-01-15T10:35:00.123456"
}
```

- **响应头**:

```
Content-Type: audio/mpeg
X-Task-Id: tts_task_abc123def456
```

- **错误响应示例**:

```json
{
    "detail": "文本转语音失败: 输入文本UTF-8编码后长度为1500字节，超过最大限制1024字节"
}
```

---

### 5. 会话管理接口

#### 5.1 获取会话信息

- **接口**: `GET /session/{session_id}/info`
- **描述**: 获取指定会话的详细信息
- **路径参数**:
  - `session_id`: 会话唯一标识符

- **响应示例**:

```json
{
    "session_id": "demo_session_1",
    "user_id": "user123",
    "conversation_id": "conv_789xyz",
    "last_activity": "2024-01-15T10:30:15.123456",
    "message_count": 5,
    "status": "active"
}
```

- **curl示例**:

```bash
curl "http://localhost:6001/session/my_session/info"
```

#### 5.2 清除会话

- **接口**: `POST /session/{session_id}/clear`
- **描述**: 清除指定会话的历史记录
- **路径参数**:
  - `session_id`: 会话唯一标识符

- **响应示例**:

```json
{
    "message": "会话已成功清除",
    "session_id": "demo_session_1",
    "cleared_at": "2024-01-15T10:35:00.123456"
}
```

- **curl示例**:

```bash
curl -X POST "http://localhost:6001/session/my_session/clear"
```

---

## Python客户端示例

### 基础聊天客户端

```python
import requests
import json

class CozeChatClient:
    def __init__(self, base_url="http://localhost:6001"):
        self.base_url = base_url
    
    def chat_sync(self, message, session_id=None):
        """同步聊天"""
        url = f"{self.base_url}/chat"
        data = {
            "message": message,
            "session_id": session_id
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def chat_stream(self, message, session_id=None):
        """流式聊天"""
        url = f"{self.base_url}/chat/stream"
        data = {
            "message": message,
            "session_id": session_id
        }
        
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        full_content = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = json.loads(line_str[6:])
                    if data['type'] == 'chunk':
                        content = data['data']['content']
                        print(content, end='', flush=True)
                        full_content += content
                    elif data['type'] == 'complete':
                        print("\n")
                        break
        return full_content
    
    def analyze_emotion(self, text, user_id=None, session_id=None):
        """情绪分析"""
        url = f"{self.base_url}/analyze-emotion"
        data = {
            "text": text,
            "session_id": session_id
        }
        if user_id:
            data["user_id"] = user_id
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def text_to_speech(self, text, voice_id=None, emotion=None, emotion_scale=4.0, output_path=None):
        """文本转语音"""
        url = f"{self.base_url}/text-to-speech"
        data = {
            "input": text,
            "emotion": emotion,
            "emotion_scale": emotion_scale
        }
        if voice_id:
            data["voice_id"] = voice_id
        
        # 获取音频流
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        # 保存为文件或返回音频流
        if output_path:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            return output_path
        else:
            return response.content

# 使用示例
client = CozeChatClient()

# 同步聊天
result = client.chat_sync("你好，我想聊聊工作压力")
print(f"回复: {result['response']}")

# 流式聊天
client.chat_stream("能给我一些缓解压力的建议吗？")

# 情绪分析
emotion_result = client.analyze_emotion("我最近工作压力很大，感觉很焦虑")
print(f"情绪标签: {emotion_result['emotion_tags']}")
print(f"分析结果: {emotion_result['analysis_result']}")

# 文本转语音
audio_path = client.text_to_speech("今天天气很好", output_path="output.mp3")
print(f"音频文件保存到: {audio_path}")
```

---

## 流式输出详细说明

### SSE事件类型

| 事件类型 | 描述 | 数据结构 |
|---------|------|----------|
| `chunk` | 数据块 | `{"type": "chunk", "data": {"content": "...", "chunk_index": 0}}` |
| `complete` | 完成 | `{"type": "complete", "data": {"total_chunks": 5, "full_content": "..."}}` |
| `error` | 错误 | `{"type": "error", "data": {"message": "错误信息"}}` |

### 前端JavaScript示例

```javascript
async function streamChat(message) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            session_id: 'web_session_1'
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let fullContent = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.type === 'chunk') {
                        const content = data.data.content;
                        fullContent += content;
                        // 实时更新UI
                        updateChatDisplay(content, false);
                    } else if (data.type === 'complete') {
                        updateChatDisplay('', true);
                        console.log('完整回复:', fullContent);
                    }
                } catch (e) {
                    console.error('解析SSE数据失败:', e);
                }
            }
        }
    }
}
```

---

## 配置说明

### 环境变量配置

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `COZE_API_TOKEN` | Coze API访问令牌 | - | ✅ |
| `COZE_BOT_ID` | Coze机器人ID | - | ✅ |
| `COZE_USER_ID` | 用户标识 | `default_user` | ❌ |
| `COZE_BASE_URL` | API基础地址 | `https://api.coze.cn/v3` | ❌ |
| `SERVER_HOST` | 服务器监听地址 | `0.0.0.0` | ❌ |
| `SERVER_PORT` | 服务器端口 | `6001` | ❌ |
| `DEBUG` | 调试模式 | `false` | ❌ |

### 服务器配置

```python
SERVER_CONFIG = {
    'host': '0.0.0.0',           # 监听所有网卡
    'port': 6001,                # 端口号
    'debug': False,              # 调试模式
    'allowed_origins': ['*'],    # CORS允许源
    'max_request_size': 10485760 # 最大请求大小(10MB)
}
```

---

## 错误处理

### HTTP状态码

| 状态码 | 描述 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 请求参数错误 | 检查请求体格式和必需字段 |
| 500 | 服务器内部错误 | 查看服务器日志，检查Coze API配置 |
| 503 | 服务不可用 | 检查Coze API服务状态 |

### 错误响应格式

```json
{
    "detail": "错误描述信息"
}
```

### 常见错误

1. **Coze API认证失败**
   ```
   {"detail": "Coze API请求失败: 401 Unauthorized"}
   ```
   **解决方案**: 检查`COZE_API_TOKEN`是否正确

2. **Bot ID无效**
   ```
   {"detail": "Coze API请求失败: 400 Bad Request"}
   ```
   **解决方案**: 检查`COZE_BOT_ID`是否正确

3. **请求超时**
   ```
   {"detail": "同步聊天失败: timeout"}
   ```
   **解决方案**: 增加请求超时时间或检查网络连接

4. **文本转语音错误**

#### 4.1 文本过长
   ```
   {"detail": "文本转语音失败: 输入文本UTF-8编码后长度为1500字节，超过最大限制1024字节"}
   ```
   **解决方案**: 缩短输入文本长度，或分段转换文本

#### 4.2 无效音色ID
   ```
   {"detail": "文本转语音失败: 音色ID 'invalid_voice_id' 无效"}
   ```
   **解决方案**: 使用有效的音色ID，可通过Coze音色列表API获取

#### 4.3 情感设置无效
   ```
   {"detail": "文本转语音失败: 无效的情感类型 'unknown'，支持的枚举值：happy, sad, angry, surprised, fear, hate, excited, coldness, neutral"}
   ```
   **解决方案**: 使用指定的情感枚举值之一

#### 4.4 情感强度超出范围
   ```
   {"detail": "文本转语音失败: 情感强度需在 1.0~5.0 之间"}
   ```
   **解决方案**: 将emotion_scale参数设置为1.0~5.0之间的值

#### 4.5 权限不足
   ```
   {"detail": "文本转语音失败: 访问被拒绝"}
   ```
   **解决方案**: 确保COZE_API_TOKEN已开通createSpeech权限（在Coze平台令牌管理中检查）

5. **情绪分析错误**

#### 5.1 输入文本为空
   ```
   {"detail": "情绪分析失败: 输入文本不能为空"}
   ```
   **解决方案**: 提供有效的文本内容进行分析

#### 5.2 Coze API调用失败
   ```
   {"detail": "情绪分析失败: Coze API调用失败: 401 Unauthorized"}
   ```
   **解决方案**: 检查COZE_API_TOKEN是否正确，确保API密钥有效

#### 5.3 文本过长
   ```
   {"detail": "情绪分析失败: 文本长度超过限制"}
   ```
   **解决方案**: 缩短输入文本或分段分析

#### 5.4 响应格式错误
   ```
   {"detail": "情绪分析失败: 无法解析Coze API响应"}
   ```
   **解决方案**: 检查Coze API服务状态，稍后重试

#### 5.5 网络超时
   ```
   {"detail": "情绪分析失败: 请求超时"}
   ```
   **解决方案**: 增加请求超时时间或检查网络连接

---

## 性能优化

### 并发处理

- 使用异步处理提高并发性能
- 支持多个同时进行的流式聊天会话
- 会话隔离，避免消息混淆

### 资源管理

- 自动管理会话映射和清理
- 流式响应减少内存占用
- 请求限流避免API调用过频
- TTS服务采用流式传输，提高响应速度
- 音频文件及时释放内存资源

### 监控建议

1. **日志监控**: 查看`logs/api_server.log`
2. **性能指标**: 监控响应时间和并发数
3. **错误率**: 关注5xx错误出现频率
4. **资源使用**: 监控CPU和内存使用情况

---

## 最佳实践

### 1. 会话管理

```python
# 使用固定session_id维持对话上下文
session_id = "user_session_123"

# 第一轮对话
response1 = client.chat_sync("你好", session_id)
# 第二轮对话（自动使用上下文）
response2 = client.chat_sync("我刚才说了什么？", session_id)
```

### 2. 流式处理

```python
# 前端实时显示
def process_stream(response):
    for chunk in response.iter_lines():
        if chunk:
            data = json.loads(chunk.decode('utf-8')[6:])
            if data['type'] == 'chunk':
                display_chunk(data['data']['content'])
```

### 3. 错误重试

```python
import time
import random

def retry_request(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt + random.uniform(0, 1))
```

### 4. 超时配置

```python
# 同步请求超时
requests.post(url, json=data, timeout=60)

# 流式请求不设超时，但要有结束条件
response = requests.post(url, json=data, stream=True, timeout=None)
```

### 5. TTS使用建议

```python
# 文本分段转换长文本
def tts_long_text(text, chunk_size=200):
    """将长文本分段转换为音频"""
    words = text.split()
    chunks = []
    current_chunk = ""
    
    for word in words:
        if len(current_chunk + word) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            current_chunk += " " + word
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    audio_files = []
    for i, chunk in enumerate(chunks):
        audio_path = client.text_to_speech(chunk, output_path=f"chunk_{i}.mp3")
        audio_files.append(audio_path)
    
    return audio_files

# 自定义语音参数
def tts_with_emotion(text, emotion="happy", scale=4.0):
    """使用情感参数进行TTS"""
    return client.text_to_speech(
        text=text,
        emotion=emotion,
        emotion_scale=scale,
        output_path="emotional_speech.mp3"
    )
```

---

## 更新日志

### v1.3.0 (2024-01-20)

- 🎉 新增情绪标签识别功能
- ✨ 基于Coze API的智能情绪分析
- 🔧 支持情绪强度评估和置信度计算
- 📖 完善情绪分析相关错误处理文档
- 🚀 增加情绪分析最佳实践指南
- 🛡️ 整合情绪分析与聊天功能，提供完整的心理健康服务

### v1.2.0 (2024-01-20)

- 🎉 新增文本转语音（TTS）功能
- ✨ 支持多种情感语音合成（快乐、悲伤、愤怒、惊讶等）
- 🔧 支持自定义音色和情感强度
- 📖 完善TTS相关错误处理文档
- 🚀 优化音频流处理性能
- 🛡️ 增加TTS使用最佳实践指南

### v1.0.0 (2024-01-15)

- 🎉 首次发布
- ✨ 支持同步和流式聊天
- 🔧 完整的会话管理功能
- 📖 自动化API文档
- 🚀 基于FastAPI的高性能实现
- 🔄 实时SSE流式输出
- 🛡️ 完善的错误处理机制

---

## 技术支持

- **API文档**: `http://localhost:6001/docs`
- **健康检查**: `http://localhost:6001/health`
- **日志文件**: `logs/api_server.log`
- **配置示例**: `.env.example`

---

*本文档版本: v1.3.0*  
*最后更新: 2024年1月20日*
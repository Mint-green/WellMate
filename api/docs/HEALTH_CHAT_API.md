# 健康对话 API 文档

## 概述
健康对话模块提供通用的健康相关文本对话接口，支持流式和非流式两种响应方式。

## 接口列表

### 健康文本对话（非流式）
- **接口地址**: `POST /api/v1/health/chat/text`
- **功能描述**: 健康相关的文本对话接口，返回完整响应
- **请求参数**:
  ```json
  {
    "message": "string",
    "session_id": "string（可选）"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "健康对话处理完成",
    "data": {
      "response": "string",
      "user_input": "string"
    }
  }
  ```

### 健康文本对话（流式）
- **接口地址**: `POST /api/v1/health/chat/text/stream`
- **功能描述**: 健康相关的文本对话接口，支持Server-Sent Events流式响应
- **请求参数**:
  ```json
  {
    "message": "string",
    "session_id": "string（可选）"
  }
  ```
- **响应格式** (SSE格式):
  ```
  event: status
  data: {"status": "success", "message": "流式对话开始"}
  
  event: message
  data: {"content": "响应内容", "user_input": "用户输入"}
  
  event: complete
  data: {"status": "success", "message": "流式对话完成"}
  ```

## 错误码
- `400`: 请求参数错误
- `500`: 服务器内部错误

## 使用示例
```python
import requests

# 非流式对话
response = requests.post('http://localhost:5000/api/v1/health/chat/text', json={
    'message': '我感觉有点头痛，应该怎么办？'
})

# 流式对话（使用SSE客户端）
import sseclient

response = requests.post('http://localhost:5000/api/v1/health/chat/text/stream', 
                       json={'message': '头痛建议'}, stream=True)
client = sseclient.SSEClient(response)
for event in client.events():
    print(f"Event: {event.event}, Data: {event.data}")
```

## 注意事项
1. 流式接口适合需要实时响应的场景
2. 非流式接口适合需要完整响应的场景
3. 建议使用session_id来维护对话上下文
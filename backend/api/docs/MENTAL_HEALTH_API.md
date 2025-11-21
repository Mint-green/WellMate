# 心理健康会话 API 文档

## 概述
心理健康会话模块专门处理与心理健康相关的对话，包括情绪管理、压力缓解、心理疏导等话题。

## 接口列表

### 心理健康文本对话（非流式）
- **接口地址**: `POST /api/v1/health/mental/chat`
- **功能描述**: 心理健康相关的文本对话接口，返回完整响应
- **请求参数**:
  ```json
  {
    "text": "string",
    "session_id": "string（可选）"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "心理健康对话处理完成",
    "data": {
      "response": "string",
      "user_input": "string",
      "category": "mental",
      "conversation_id": "string",
      "session_id": "string",
      "is_new_session": "boolean"
    }
  }
  ```

### 心理健康文本对话（流式）
- **接口地址**: `POST /api/v1/health/mental/chat/stream`
- **功能描述**: 心理健康相关的文本对话接口，支持Server-Sent Events流式响应
- **请求参数**:
  ```json
  {
    "text": "string",
    "session_id": "string（可选）"
  }
  ```
- **响应格式** (SSE格式):
  ```
  event: status
  data: {"status": "success", "message": "心理健康流式对话开始"}
  
  event: message
  data: {"content": "响应内容", "user_input": "用户输入", "category": "mental", "conversation_id": "string", "session_id": "string", "is_new_session": "boolean"}
  
  event: complete
  data: {"status": "success", "message": "心理健康流式对话完成"}
  ```

### 文字转语音接口
- **接口地址**: `POST /api/v1/health/mental/text-to-speech`
- **功能描述**: 将文本转换为语音，用于心理健康对话的语音回复
- **请求参数**:
  ```json
  {
    "text": "需要转换为语音的文本内容"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "语音合成成功",
    "data": {
      "audio": "base64编码的音频数据",
      "text": "原始文本",
      "type": "mental"
    }
  }
  ```

### 情绪分析接口
- **接口地址**: `POST /api/v1/health/mental/emotion-analysis`
- **功能描述**: 分析用户输入文本的情绪状态
- **请求参数**:
  ```json
  {
    "text": "需要分析情绪的文本",
    "session_id": "string（可选）"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "情绪分析完成",
    "data": {
      "emotion_analysis": "情绪分析结果",
      "input_text": "原始文本",
      "session_id": "会话ID",
      "token_usage": "token使用量"
    }
  }
  ```

## 支持的健康话题
- 情绪管理与调节
- 压力缓解技巧
- 焦虑抑郁疏导
- 人际关系咨询
- 自我认知与成长
- 睡眠心理改善
- 工作生活平衡

## 错误码
- `400`: 请求参数错误
- `500`: 服务器内部错误

## 会话管理机制

### 会话ID和对话ID的区别与关联
- **session_id**: 系统生成的本地会话标识符，用于维护对话上下文和消息存储
- **conversation_id**: AI模型使用的对话标识符，用于保持与AI模型的对话连续性
- **自动绑定机制**: 客户端只需传递session_id，系统会自动绑定对应的conversation_id

### 会话创建和复用
- **首次请求**: 不提供session_id时，系统自动创建新会话并返回session_id和conversation_id
- **会话复用**: 提供有效的session_id时，系统自动获取绑定的conversation_id继续对话
- **自动绑定**: 系统自动管理session_id与conversation_id的关联，客户端无需关心conversation_id
- **无效会话处理**: 提供无效session_id时，系统自动创建新会话替代

### 响应字段说明
- `conversation_id`: AI模型使用的对话标识符，由系统自动管理
- `session_id`: 本地会话ID，客户端应保存此ID用于后续对话
- **简化使用**: 客户端只需保存session_id，无需保存conversation_id

## 使用示例
```python
import requests

# 心理健康非流式对话（首次请求，创建新会话）
response = requests.post('http://localhost:5000/api/v1/health/mental/chat', json={
    'text': '我最近感觉很焦虑，有什么缓解方法？'
})

if response.status_code == 200:
    result = response.json()
    session_id = result['data']['session_id']
    conversation_id = result['data']['conversation_id']
    is_new = result['data']['is_new_session']
    print(f"会话ID: {session_id}, 对话ID: {conversation_id}, 是否新会话: {is_new}")
    
    # 继续对话（使用相同session_id，系统自动绑定conversation_id）
    response2 = requests.post('http://localhost:5000/api/v1/health/mental/chat', json={
        'text': '焦虑时应该怎么调整心态？',
        'session_id': session_id
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        is_new2 = result2['data']['is_new_session']
        print(f"继续对话，是否新会话: {is_new2}")

# 心理健康流式对话
response = requests.post('http://localhost:5000/api/v1/health/mental/chat/stream', 
                       json={'text': '如何应对工作压力？'}, stream=True)
```

## 注意事项
1. 本模块专门处理心理健康相关话题
2. 身体健康相关话题请使用身体健康会话模块
3. 建议使用session_id来维护对话上下文
4. 本模块提供心理支持，但不替代专业心理咨询
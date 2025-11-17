# 会话管理 API 文档

## 概述
会话管理模块提供健康对话会话的创建、查询、删除等管理功能。

## 接口列表

### 获取会话列表
- **接口地址**: `GET /api/v1/health/sessions`
- **功能描述**: 获取当前用户的健康对话会话列表
- **请求参数**:
  - `user_uuid`: 用户UUID（可选，默认为当前用户）
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "获取会话列表成功",
    "data": {
      "uuid": "string",
      "sessions": [
        {
          "session_id": "string",
          "title": "string",
          "category": "physical|mental",
          "created_at": "2024-01-01T10:00:00Z",
          "last_activity": "2024-01-01T10:00:00Z",
          "message_count": 10
        }
      ]
    }
  }
  ```

### 创建新会话
- **接口地址**: `POST /api/v1/health/sessions`
- **功能描述**: 创建新的健康对话会话
- **请求参数**:
  ```json
  {
    "title": "string",
    "category": "physical|mental"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "会话创建成功",
    "data": {
      "session_id": "string",
      "title": "string",
      "category": "physical|mental",
      "created_at": "2024-01-01T10:00:00Z"
    }
  }
  ```

### 删除会话
- **接口地址**: `DELETE /api/v1/health/sessions/<session_id>`
- **功能描述**: 删除指定的健康对话会话
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "会话删除成功",
    "data": {
      "deleted_session_id": "string"
    }
  }
  ```

### 获取会话详情
- **接口地址**: `GET /api/v1/health/sessions/<session_id>`
- **功能描述**: 获取指定会话的详细信息
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "获取会话详情成功",
    "data": {
      "session_id": "string",
      "title": "string",
      "category": "physical|mental",
      "created_at": "2024-01-01T10:00:00Z",
      "messages": [
        {
          "message_id": "string",
          "role": "user|assistant",
          "content": "string",
          "timestamp": "2024-01-01T10:00:00Z"
        }
      ]
    }
  }
  ```

## 错误码
- `400`: 请求参数错误
- `404`: 会话不存在
- `500`: 服务器内部错误

## 使用示例
```python
import requests

# 设置认证头
headers = {'Authorization': 'Bearer <access_token>'}

# 获取会话列表
response = requests.get('http://localhost:5000/api/v1/health/sessions', headers=headers)

# 创建新会话
response = requests.post('http://localhost:5000/api/v1/health/sessions', 
                       headers=headers,
                       json={
                           'title': '头痛咨询',
                           'category': 'physical'
                       })

# 删除会话
session_id = 'session_123'
response = requests.delete(f'http://localhost:5000/api/v1/health/sessions/{session_id}', 
                          headers=headers)

# 获取会话详情
response = requests.get(f'http://localhost:5000/api/v1/health/sessions/{session_id}', 
                       headers=headers)

# 与physical接口集成使用
# 1. 通过会话管理创建会话
session_response = requests.post('http://localhost:5000/api/v1/health/sessions',
                               headers=headers,
                               json={'title': '运动健康咨询', 'category': 'physical'})

if session_response.status_code == 200:
    session_data = session_response.json()['data']
    session_id = session_data['session_id']
    
    # 2. 使用创建的session_id进行健康对话
    chat_response = requests.post('http://localhost:5000/api/v1/health/physical/text',
                                headers=headers,
                                json={
                                    'message': '如何制定运动计划？',
                                    'session_id': session_id
                                })
    
    if chat_response.status_code == 200:
        chat_data = chat_response.json()
        print(f"对话成功，会话ID: {chat_data['data']['session_id']}")
```

## 会话分类说明
- `physical`: 身体健康相关会话
- `mental`: 心理健康相关会话
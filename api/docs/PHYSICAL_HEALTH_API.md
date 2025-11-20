# 身体健康会话 API 文档

## 概述
身体健康会话模块专门处理与身体健康相关的对话，包括身体症状、运动健康、营养饮食等话题。该模块采用JWT token认证机制，支持会话管理和对话连续性。

## 认证要求
所有身体健康会话接口都需要JWT token认证。请在请求头中添加：
```
Authorization: Bearer <access_token>
```

## 接口列表

### 身体健康文本对话（非流式）
- **接口地址**: `POST /api/v1/health/physical/chat`
- **功能描述**: 身体健康相关的文本对话接口，返回完整响应
- **认证要求**: JWT token认证
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
    "message": "身体健康对话处理完成",
    "data": {
      "response": "string",
      "user_input": "string",
      "category": "physical",
      "conversation_id": "string",
      "session_id": "string",
      "is_new_session": "boolean"
    }
  }
  ```

### 身体健康文本对话（流式）
- **接口地址**: `POST /api/v1/health/physical/chat/stream`
- **功能描述**: 身体健康相关的文本对话接口，支持Server-Sent Events流式响应
- **认证要求**: JWT token认证
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
  data: {"status": "success", "message": "身体健康流式对话开始"}
  
  event: message
  data: {"content": "响应内容", "user_input": "用户输入", "category": "physical", "conversation_id": "string", "session_id": "string", "is_new_session": "boolean"}
  
  event: complete
  data: {"status": "success", "message": "身体健康流式对话完成"}
  ```

## 支持的健康话题
- 身体症状咨询（头痛、发热、咳嗽等）
- 运动健康指导
- 营养饮食建议
- 睡眠质量改善
- 慢性病管理
- 体检报告解读

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

### 基础使用（带认证）
```python
import requests

# 1. 用户登录获取token
login_response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'username': 'demo_user',
    'password': 'demo_pass'
})

if login_response.status_code == 200:
    token_data = login_response.json()['data']
    access_token = token_data['access_token']
    
    # 2. 设置认证头
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # 3. 身体健康非流式对话（首次请求，创建新会话）
    response = requests.post('http://localhost:5000/api/v1/health/physical/chat', 
                           headers=headers,
                           json={'text': '我最近经常头痛，应该注意什么？'})
    
    if response.status_code == 200:
        result = response.json()
        session_id = result['data']['session_id']
        is_new = result['data']['is_new_session']
        print(f"会话ID: {session_id}, 是否新会话: {is_new}")
        
        # 4. 继续对话（使用相同session_id）
        response2 = requests.post('http://localhost:5000/api/v1/health/physical/chat',
                                headers=headers,
                                json={
                                    'text': '头痛时应该吃什么药？',
                                    'session_id': session_id
                                })
        
        if response2.status_code == 200:
            result2 = response2.json()
            is_new2 = result2['data']['is_new_session']
            print(f"继续对话，是否新会话: {is_new2}")

# 身体健康流式对话
response = requests.post('http://localhost:5000/api/v1/health/physical/chat/stream', 
                       headers=headers,
                       json={'text': '运动后肌肉酸痛怎么办？'}, 
                       stream=True)
```

### 错误处理示例
```python
# 处理认证失败
if response.status_code == 401:
    print("认证失败，请重新登录获取token")
    
# 处理无效会话ID
if response.status_code == 200:
    result = response.json()
    if result['data']['is_new_session']:
        print("系统自动创建了新会话")
```

## 注意事项
1. **认证要求**: 所有接口都需要有效的JWT token认证
2. **会话连续性**: 使用session_id维护对话上下文，提高用户体验
3. **自动会话管理**: 系统自动处理无效会话，确保服务可用性
4. **话题专注**: 本模块专门处理身体健康相关话题，心理健康请使用心理健康会话模块
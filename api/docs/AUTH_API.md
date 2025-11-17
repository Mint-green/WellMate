# 认证管理 API 文档

## 概述
认证管理模块提供用户注册、登录、JWT token管理等相关接口。采用JWT（JSON Web Token）无状态认证机制，支持双token（access token + refresh token）设计。

## JWT Token 机制

### Token 类型
- **Access Token**: 用于API访问认证，有效期24小时
- **Refresh Token**: 用于刷新access token，有效期7天

### Token 存储和校验
- **客户端存储**: access token存储在客户端（localStorage/sessionStorage/HTTP-only Cookie）
- **服务器无状态**: 服务器不存储token，通过签名验证token有效性
- **自包含设计**: token包含用户ID、用户名、过期时间等完整信息

### 请求头格式
```
Authorization: Bearer <access_token>
```

## 接口列表

### 用户注册
- **接口地址**: `POST /api/v1/auth/register`
- **功能描述**: 用户注册，创建新账户
- **请求参数**:
  ```json
  {
    "username": "string",
    "password": "string", 
    "full_name": "string",
    "gender": "male|female|other",
    "birth_date": "YYYY-MM-DD",
    "age": "integer",
    "settings": "object"
  }
  ```
- **必需字段**: `username`, `password`, `full_name`
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "用户注册成功",
    "data": {
        "uuid": "string",
        "username": "string"
      }
  }
  ```
### 用户登录
- **接口地址**: `POST /api/v1/auth/login`
- **功能描述**: 用户登录接口，返回双token
- **请求参数**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "登录成功",
    "data": {
        "uuid": "string",
        "username": "string",
        "full_name": "string",
        "access_token": "string",
        "refresh_token": "string",
        "token_type": "Bearer",
        "expires_in": 900
      }
  }
  ```

### Token 刷新
- **接口地址**: `POST /api/v1/auth/refresh`
- **功能描述**: 使用refresh token刷新access token
- **请求参数**:
  ```json
  {
    "refresh_token": "string"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "token刷新成功",
    "data": {
      "access_token": "string",
      "refresh_token": "string"
    }
  }
  ```

### Token 验证
- **接口地址**: `GET /api/v1/auth/verify`
- **功能描述**: 验证access token有效性
- **请求头**:
  ```
  Authorization: Bearer <access_token>
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "token有效",
    "data": {
      "uuid": "string",
      "username": "string",
      "expires_at": "2024-01-01T10:00:00Z"
    }
  }
  ```

## 错误码

### 通用错误码
- `400`: 请求参数错误
- `401`: 认证失败
- `409`: 用户已存在

### JWT Token 相关错误码
- `MISSING_TOKEN`: 缺少认证token
- `INVALID_TOKEN_FORMAT`: token格式错误，应为Bearer格式
- `INVALID_TOKEN`: token无效或已过期
- `INVALID_TOKEN_TYPE`: token类型错误，需要access token

## Token 校验流程

1. **提取Token**: 从Authorization头提取Bearer token
2. **验证签名**: 使用服务器密钥验证token签名
3. **检查类型**: 确保是access token（非refresh token）
4. **验证过期**: 检查token是否在有效期内
5. **注入上下文**: 将用户信息注入请求上下文

## 使用示例

### 用户注册和登录
```python
import requests

# 用户注册
response = requests.post('http://localhost:5000/api/v1/auth/register', json={
    'username': 'testuser',
    'password': 'password123',
    'full_name': '测试用户'
})

# 用户登录
response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'username': 'testuser',
    'password': 'password123'
})

# 获取双token
if response.status_code == 200:
    result = response.json()
    access_token = result['data']['access_token']
    refresh_token = result['data']['refresh_token']
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
```

### 访问受保护接口
```python
import requests

# 设置请求头
headers = {
    'Authorization': f'Bearer {access_token}'
}

# 获取用户信息
response = requests.get('http://localhost:5000/api/v1/users/profile', headers=headers)
if response.status_code == 200:
    user_info = response.json()
    print(f"用户信息: {user_info}")

# 访问身体健康会话接口（需要认证）
response = requests.post('http://localhost:5000/api/v1/health/physical/text', 
                       headers=headers,
                       json={'message': '头痛咨询'})
if response.status_code == 200:
    health_response = response.json()
    print(f"健康咨询回复: {health_response}")
```

### Token 刷新
```python
# 当access token过期时，使用refresh token刷新
response = requests.post('http://localhost:5000/api/v1/auth/refresh', json={
    'refresh_token': refresh_token
})

if response.status_code == 200:
    result = response.json()
    new_access_token = result['data']['access_token']
    new_refresh_token = result['data']['refresh_token']
    print("Token刷新成功")
```

## 安全说明

- **签名验证**: 使用HMAC-SHA256算法确保token完整性
- **过期机制**: access token 24小时过期，降低安全风险
- **双token设计**: refresh token仅用于token刷新，不直接访问业务接口
- **错误处理**: 详细的错误码和错误信息，便于客户端处理
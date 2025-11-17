# 用户管理 API 文档

## 概述
用户管理模块提供用户信息管理、配置设置等接口。所有接口均受JWT token保护，需要有效的access token才能访问。

## 认证要求

所有用户管理接口都需要在请求头中包含有效的JWT access token：
```
Authorization: Bearer <access_token>
```

### Token 验证流程
1. **提取Token**: 从Authorization头提取Bearer token
2. **验证签名**: 使用服务器密钥验证token签名
3. **检查类型**: 确保是access token（非refresh token）
4. **验证过期**: 检查token是否在有效期内（24小时）
5. **注入上下文**: 将用户信息注入请求上下文

## 接口列表

### 获取用户信息
- **接口地址**: `GET /api/v1/users/profile`
- **功能描述**: 获取当前登录用户的详细信息
- **认证要求**: ✅ 需要有效的access token
- **请求头**:
  ```
  Authorization: Bearer <access_token>
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "获取用户信息成功",
    "data": {
      "uuid": "string",
      "username": "string",
      "full_name": "string",
      "gender": "string",
      "age": "integer",
      "birth_date": "string",
      "uuid": "string",
      "is_active": "boolean",
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  }
  ```

### 更新用户配置
- **接口地址**: `PUT /api/v1/users/settings`
- **功能描述**: 更新用户个人配置
- **认证要求**: ✅ 需要有效的access token
- **请求头**:
  ```
  Authorization: Bearer <access_token>
  ```
- **请求参数**:
  ```json
  {
    "language": "zh-CN",
    "theme": "dark",
    "notifications": {
      "email": true,
      "push": false
    }
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "配置更新成功",
    "data": {
      "updated_settings": ["language", "theme", "notifications"]
    }
  }
  ```

### 更新用户基本信息
- **接口地址**: `PUT /api/v1/users/profile`
- **功能描述**: 更新用户基本信息（姓名、性别、年龄等）
- **认证要求**: ✅ 需要有效的access token
- **请求头**:
  ```
  Authorization: Bearer <access_token>
  ```
- **请求参数**:
  ```json
  {
    "full_name": "string",
    "gender": "string",
    "age": "integer",
    "birth_date": "string"
  }
  ```
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "用户信息更新成功",
    "data": {
      "uuid": "string",
      "updated_fields": ["full_name", "gender", "age", "birth_date"]
    }
  }
  ```

## 错误码

### 认证相关错误
- `401`: 未授权访问
  - `MISSING_TOKEN`: 缺少认证token
  - `INVALID_TOKEN_FORMAT`: token格式错误
  - `INVALID_TOKEN`: token无效或已过期
  - `INVALID_TOKEN_TYPE`: token类型错误

### 业务相关错误
- `403`: 权限不足
- `404`: 用户不存在
- `400`: 请求参数错误
- `500`: 服务器内部错误

## Token 过期处理

当access token过期时（24小时有效期），客户端应该：

1. **检测到401错误**：接口返回`INVALID_TOKEN`错误码
2. **使用refresh token刷新**：调用`/api/v1/auth/refresh`接口获取新的access token
3. **重试请求**：使用新的access token重新调用用户接口

## 使用示例

### 完整使用流程示例
```python
import requests

# 用户注册
register_data = {
    "username": "testuser",
    "password": "password123",
    "full_name": "测试用户"
}
response = requests.post("http://127.0.0.1:5000/api/v1/auth/register", json=register_data)
print("注册结果:", response.json())

# 用户登录
login_data = {
    "username": "testuser", 
    "password": "password123"
}
response = requests.post("http://127.0.0.1:5000/api/v1/auth/login", json=login_data)
result = response.json()
print("登录结果:", result)

# 获取用户信息（需要token）
if result['status'] == 'success':
    token = result['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://127.0.0.1:5000/api/v1/users/profile", headers=headers)
    print("用户信息:", response.json())
```

### 更新用户配置
```python
import requests

headers = {'Authorization': 'Bearer your_access_token_here'}

# 更新用户配置
response = requests.put('http://localhost:5000/api/v1/users/settings', 
                       headers=headers,
                       json={
                           'language': 'zh-CN',
                           'theme': 'dark'
                       })

if response.status_code == 200:
    print("配置更新成功")
else:
    print(f"更新失败: {response.status_code}")
```

### Token 过期处理示例
```python
import requests

def get_user_profile_with_retry(access_token, refresh_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # 第一次尝试
    response = requests.get('http://localhost:5000/api/v1/users/profile', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    
    # 如果token过期，尝试刷新
    if response.status_code == 401:
        refresh_response = requests.post('http://localhost:5000/api/v1/auth/refresh', 
                                       json={'refresh_token': refresh_token})
        
        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()['data']
            # 使用新的access token重试
            headers = {'Authorization': f'Bearer {new_tokens["access_token"]}'}
            response = requests.get('http://localhost:5000/api/v1/users/profile', headers=headers)
            
            if response.status_code == 200:
                return response.json()
    
    return None
```
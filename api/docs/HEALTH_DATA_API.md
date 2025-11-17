# 健康数据 API 文档

## 概述
健康数据模块提供健康数据的查询接口，支持多种健康指标的数据获取。所有接口均受JWT token保护，需要有效的access token才能访问。

## 认证要求

所有健康数据接口都需要在请求头中包含有效的JWT access token：
```
Authorization: Bearer <access_token>
```

### Token 验证流程
1. **提取Token**: 从Authorization头提取Bearer token
2. **验证签名**: 使用服务器密钥验证token签名
3. **检查类型**: 确保是access token（非refresh token）
4. **验证过期**: 检查token是否在有效期内（24小时）
5. **注入上下文**: 将用户信息注入请求上下文，自动关联用户ID

## 接口列表

### 获取健康数据
- **接口地址**: `GET /api/v1/health/data`
- **功能描述**: 查询当前登录用户的健康数据
- **认证要求**: ✅ 需要有效的access token
- **请求头**:
  ```
  Authorization: Bearer <access_token>
  ```
- **请求参数**:
  - `type`: 数据类型（可选，默认'all'）
    - `all`: 所有数据
    - `heart_rate`: 心率数据
    - `steps`: 步数数据
    - `sleep`: 睡眠数据
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "获取健康数据成功",
    "data": {
      "uuid": "string",
      "data_type": "all|heart_rate|steps|sleep",
      "health_data": {
        "heart_rate": {
          "current": 72,
          "trend": "stable|increasing|decreasing",
          "last_updated": "2024-01-01T10:00:00Z"
        },
        "steps": {
          "today": 8500,
          "goal": 10000,
          "completion_rate": 0.85,
          "last_updated": "2024-01-01T10:00:00Z"
        },
        "sleep": {
          "last_night": 7.5,
          "quality": "good|fair|poor",
          "deep_sleep": 2.5,
          "light_sleep": 5.0,
          "last_updated": "2024-01-01T10:00:00Z"
        }
      }
    }
  }
  ```

## 支持的健康指标

### 心率数据
- **current**: 当前心率值（次/分钟）
- **trend**: 心率趋势（稳定/上升/下降）
- **last_updated**: 最后更新时间

### 步数数据
- **today**: 今日步数
- **goal**: 目标步数
- **completion_rate**: 完成率
- **last_updated**: 最后更新时间

### 睡眠数据
- **last_night**: 昨晚睡眠时长（小时）
- **quality**: 睡眠质量（好/一般/差）
- **deep_sleep**: 深睡时长（小时）
- **light_sleep**: 浅睡时长（小时）
- **last_updated**: 最后更新时间

## 错误码

### 认证相关错误
- `401`: 未授权访问
  - `MISSING_TOKEN`: 缺少认证token
  - `INVALID_TOKEN_FORMAT`: token格式错误
  - `INVALID_TOKEN`: token无效或已过期
  - `INVALID_TOKEN_TYPE`: token类型错误

### 业务相关错误
- `400`: 请求参数错误
- `404`: 用户不存在或数据未找到
- `500`: 服务器内部错误

## Token 过期处理

当access token过期时（24小时有效期），客户端应该：

1. **检测到401错误**：接口返回`INVALID_TOKEN`错误码
2. **使用refresh token刷新**：调用`/api/v1/auth/refresh`接口获取新的access token
3. **重试请求**：使用新的access token重新调用健康数据接口

## 使用示例

### 获取健康数据（需要token认证）
```python
import requests

# 设置请求头（使用有效的access token）
headers = {'Authorization': 'Bearer your_access_token_here'}

# 获取所有健康数据（无需提供uuid，自动从token获取）
response = requests.get('http://localhost:5000/api/v1/health/data', 
                       headers=headers,
                       params={'type': 'all'})

if response.status_code == 200:
    health_data = response.json()
    print(f"健康数据: {health_data}")
elif response.status_code == 401:
    error_info = response.json()
    print(f"认证失败: {error_info['error_code']} - {error_info['message']}")
    # 需要刷新token或重新登录

# 获取心率数据
response = requests.get('http://localhost:5000/api/v1/health/data', 
                       headers=headers,
                       params={'type': 'heart_rate'})

# 获取步数数据
response = requests.get('http://localhost:5000/api/v1/health/data', 
                       headers=headers,
                       params={'type': 'steps'})

# 获取睡眠数据
response = requests.get('http://localhost:5000/api/v1/health/data', 
                       headers=headers,
                       params={'type': 'sleep'})
```

### Token 过期处理示例
```python
import requests

def get_health_data_with_retry(access_token, refresh_token, data_type='all'):
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # 第一次尝试
    response = requests.get('http://localhost:5000/api/v1/health/data', 
                           headers=headers,
                           params={'type': data_type})
    
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
            response = requests.get('http://localhost:5000/api/v1/health/data', 
                                   headers=headers,
                                   params={'type': data_type})
            
            if response.status_code == 200:
                return response.json()
    
    return None

# 使用示例
health_data = get_health_data_with_retry(access_token, refresh_token, 'heart_rate')
if health_data:
    print(f"心率数据: {health_data}")
```

## 注意事项
1. **自动用户关联**：无需提供uuid参数，系统自动从token中提取当前用户信息
2. **数据权限控制**：用户只能访问自己的健康数据，无法访问其他用户数据
3. **token保护**：所有健康数据接口都受JWT token保护，确保数据安全
4. **模拟数据**：当前版本使用模拟数据，实际使用时需要连接真实数据源
5. **token过期处理**：客户端需要实现token刷新机制，确保用户体验
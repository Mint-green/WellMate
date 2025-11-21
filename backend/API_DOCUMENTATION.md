# Health Assistant API 文档

## 基础信息
- **服务器地址**: `http://localhost:5000`
- **API版本**: v1
- **认证方式**: JWT Bearer Token

## 认证接口

### 1. 用户注册
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "full_name": "测试用户",
    "gender": "male",
    "age": 25
  }'
```

### 2. 用户登录
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. 刷新Token
```bash
curl -X POST http://localhost:5000/api/v1/auth/refresh \
  -H "Authorization: Bearer <refresh_token>"
```

## 用户管理接口

### 4. 获取用户资料
```bash
curl -X GET http://localhost:5000/api/v1/users/profile \
  -H "Authorization: Bearer <access_token>"
```

### 5. 更新用户设置
```bash
curl -X PUT http://localhost:5000/api/v1/users/settings \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "dark",
    "language": "zh-CN",
    "notifications": true
  }'
```

## 健康数据接口

### 6. 获取健康数据
```bash
curl -X GET "http://localhost:5000/api/v1/health/data?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <access_token>"
```

### 7. 添加健康数据
```bash
curl -X POST http://localhost:5000/api/v1/health/data \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "blood_pressure",
    "value": "120/80",
    "unit": "mmHg",
    "recorded_at": "2024-01-15T10:30:00Z",
    "notes": "早晨测量"
  }'
```

### 8. 获取健康统计
```bash
curl -X GET "http://localhost:5000/api/v1/health/data/stats?period=monthly" \
  -H "Authorization: Bearer <access_token>"
```

## 健康对话接口

### 9. 身体健康对话（非流式）
```bash
curl -X POST http://localhost:5000/api/v1/health/physical/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我最近经常头痛，应该注意什么？"
  }'
```

### 10. 身体健康对话（流式）
```bash
curl -X POST http://localhost:5000/api/v1/health/physical/chat/stream \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "运动后肌肉酸痛怎么办？"
  }'
```

### 11. 心理健康对话（非流式）
```bash
curl -X POST http://localhost:5000/api/v1/health/mental/chat \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我最近感觉很焦虑，有什么缓解方法？"
  }'
```

### 12. 心理健康对话（流式）
```bash
curl -X POST http://localhost:5000/api/v1/health/mental/chat/stream \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "如何应对工作压力？"
  }'
```

### 11. 会话管理

#### 会话ID和对话ID的区别与关联
- **session_id**: 系统生成的本地会话标识符，用于维护对话上下文和消息存储
- **conversation_id**: AI模型使用的对话标识符，用于保持与AI模型的对话连续性
- **自动绑定机制**: 客户端只需传递session_id，系统会自动绑定对应的conversation_id

#### 会话创建和复用
- **首次请求**: 不提供session_id时，系统自动创建新会话并返回session_id和conversation_id
- **会话复用**: 提供有效的session_id时，系统自动获取绑定的conversation_id继续对话
- **自动绑定**: 系统自动管理session_id与conversation_id的关联，客户端无需关心conversation_id
- **无效会话处理**: 提供无效session_id时，系统自动创建新会话替代

#### 简化使用流程
1. 客户端只需保存session_id用于后续对话
2. 系统自动管理conversation_id与AI模型的对话连续性
3. 支持流式和非流式对话的统一会话管理

```bash
# 获取会话列表
curl -X GET http://localhost:5000/api/v1/health/sessions \
  -H "Authorization: Bearer <access_token>"

# 创建新会话
curl -X POST http://localhost:5000/api/v1/health/sessions \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "头痛咨询",
    "category": "physical"
  }'
```

## 测试接口

### 12. 健康检查
```bash
curl -X GET http://localhost:5000/api/v1/test/health
```

### 13. 数据库连接测试
```bash
curl -X GET http://localhost:5000/api/v1/test/db
```

## 错误代码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 常见问题与解决方案

### 1. 参数错误问题
**问题描述**: `TypeError: get_profile() takes 0 positional arguments but 1 was given`

**原因分析**: 
- 使用`@token_required`装饰器的函数需要接收`current_user`参数
- 但函数定义未声明该参数，导致参数不匹配

**已修复的函数**:
- `get_profile()` → `get_profile(current_user)`
- `update_settings()` → `update_settings(current_user)`
- `get_health_data()` → `get_health_data(current_user)`
- `add_health_data()` → `add_health_data(current_user)`
- `get_health_stats()` → `get_health_stats(current_user)`

**验证状态**: ✅ 已修复并测试通过

### 2. 会话管理
**历史记录传递**: 系统自动从数据库获取历史对话记录，支持最多10轮对话的上下文传递

**会话连续性**: 使用相同的`session_id`可以保持与AI模型的对话连续性

## 请求头说明

- `Content-Type: application/json` - 请求体为JSON格式
- `Authorization: Bearer <token>` - JWT认证令牌
- `Accept: application/json` - 期望返回JSON格式

## 响应格式

成功响应格式：
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

错误响应格式：
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 使用示例

### 完整登录流程示例
```bash
# 1. 用户注册
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "demo_pass",
    "full_name": "演示用户",
    "gender": "female",
    "age": 30
  }'

# 2. 用户登录
response=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "demo_pass"
  }')

# 3. 提取access_token
token=$(echo $response | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 4. 获取用户资料
curl -X GET http://localhost:5000/api/v1/users/profile \
  -H "Authorization: Bearer $token"

# 5. 身体健康对话（首次请求，创建新会话）
response=$(curl -s -X POST http://localhost:5000/api/v1/health/physical/chat \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我最近经常头痛，应该注意什么？"
  }')

# 6. 提取会话ID和对话ID
session_id=$(echo $response | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)
conversation_id=$(echo $response | grep -o '"conversation_id":"[^"]*' | cut -d'"' -f4)
is_new_session=$(echo $response | grep -o '"is_new_session":[^,}]*' | cut -d':' -f2)
echo "会话ID: $session_id, 对话ID: $conversation_id, 是否新会话: $is_new_session"

# 7. 继续对话（使用会话ID，系统自动绑定conversation_id）
response2=$(curl -s -X POST http://localhost:5000/api/v1/health/physical/chat \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "头痛时应该吃什么药？",
    "session_id": "'$session_id'"
  }')

# 8. 验证会话连续性
is_new_session2=$(echo $response2 | grep -o '"is_new_session":[^,}]*' | cut -d':' -f2)
echo "继续对话，是否新会话: $is_new_session2"
```

### Postman导入格式

你也可以将以下JSON导入到Postman中：

```json
{
  "info": {
    "name": "Health Assistant API",
    "description": "健康助手后端API接口",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "认证接口",
      "item": [
        {
          "name": "用户注册",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"testuser\",\n  \"password\": \"password123\",\n  \"full_name\": \"测试用户\",\n  \"gender\": \"male\",\n  \"age\": 25\n}"
            },
            "url": {
              "raw": "http://localhost:5000/api/v1/auth/register",
              "protocol": "http",
              "host": ["localhost"],
              "port": "5000",
              "path": ["api", "v1", "auth", "register"]
            }
          }
        },
        {
          "name": "用户登录",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"username\": \"testuser\",\n  \"password\": \"password123\"\n}"
            },
            "url": {
              "raw": "http://localhost:5000/api/v1/auth/login",
              "protocol": "http",
              "host": ["localhost"],
              "port": "5000",
              "path": ["api", "v1", "auth", "login"]
            }
          }
        }
      ]
    }
  ]
}
```

## 注意事项

1. 所有需要认证的接口都必须包含有效的JWT令牌
2. 时间参数请使用ISO 8601格式
3. 密码传输建议在生产环境中使用HTTPS
4. 接口响应时间可能因数据库负载而异
5. 建议在请求中添加超时设置

## 更新日志

### 2024-01-15 修复更新
- **修复内容**: 解决`@token_required`装饰器参数不匹配问题
- **影响接口**: 
  - `/api/v1/users/profile` (GET)
  - `/api/v1/users/settings` (PUT) 
  - `/api/v1/health/data` (GET, POST)
  - `/api/v1/health/data/stats` (GET)
- **修复状态**: ✅ 已完全修复并测试通过
- **技术细节**: 所有使用`@token_required`装饰器的函数现在正确接收`current_user`参数

### 2024-01-14 功能增强
- **新增功能**: 历史会话记录自动传递机制
- **技术实现**: 支持最多10轮对话的上下文传递
- **会话管理**: 自动绑定`session_id`与`conversation_id`
- **数据库集成**: 完整的消息存储和检索功能
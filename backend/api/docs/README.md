# Health Assistant API 文档索引

## 概述
Health Assistant 后端API提供完整的健康管理服务，包括用户认证、健康对话、数据查询等功能。

## API 基础信息
- **基础URL**: `http://localhost:5000/api/v1`
- **当前版本**: v1.0.0
- **认证方式**: Bearer Token

## 模块文档

### 核心模块
- [认证管理 API](AUTH_API.md) - 用户注册、登录等认证功能
- [用户管理 API](USERS_API.md) - 用户信息管理和配置设置
- [测试 API](TEST_API.md) - 服务状态检查和健康监控

### 健康对话模块
- [健康对话 API](HEALTH_CHAT_API.md) - 通用健康对话接口
- [身体健康会话 API](PHYSICAL_HEALTH_API.md) - 身体健康相关对话
- [心理健康会话 API](MENTAL_HEALTH_API.md) - 心理健康相关对话
- [会话管理 API](SESSIONS_API.md) - 对话会话管理

### 数据模块
- [健康数据 API](HEALTH_DATA_API.md) - 健康数据查询接口

## API 路径结构
```
/api/v1/
├── auth/           # 认证管理
│   ├── register   # 用户注册
│   └── login      # 用户登录
├── users/         # 用户管理
│   ├── profile    # 用户信息
│   └── settings   # 用户配置
├── health/        # 健康相关
│   ├── chat/      # 通用健康对话
│   ├── physical/  # 身体健康会话
│   ├── mental/    # 心理健康会话
│   ├── sessions/  # 会话管理
│   └── data/      # 健康数据查询
└── test/          # 测试接口
    ├──            # API版本测试
    └── health     # 健康状态检查
```

## 快速开始

### 1. 启动服务
```bash
python app.py --host 127.0.0.1 --port 5000
```

### 2. 测试服务状态
```bash
# 使用curl测试
curl -X GET http://127.0.0.1:5000/api/v1/test

# 使用PowerShell测试
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/v1/test" -Method GET
```

### 3. 使用示例
```python
import requests

# 测试API
response = requests.get('http://localhost:5000/api/v1/test')
print(response.json())

# 健康对话
response = requests.post('http://localhost:5000/api/v1/health/chat/text', json={
    'message': '我感觉有点头痛，应该怎么办？'
})
print(response.json())
```

## 错误处理
所有API接口都遵循统一的响应格式：
```json
{
    "status": "success|error",
    "message": "描述性消息",
    "data": {}
}
```

## 开发说明
- 所有接口都支持CORS
- 建议使用HTTPS在生产环境
- 流式接口使用Server-Sent Events (SSE)
- 支持JSON格式的请求和响应

## 版本历史
- v1.0.0 (2024-01-01): 初始版本发布
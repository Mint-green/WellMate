# 测试 API 文档

## 概述
测试模块提供API服务状态检查和健康状态监控接口。

## 接口列表

### API版本测试
- **接口地址**: `GET /api/v1/test`
- **功能描述**: 测试API v1版本是否正常工作
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "API v1版本测试成功",
    "data": {
      "timestamp": "2024-01-01T10:00:00Z",
      "version": "v1.0.0"
    }
  }
  ```

### 健康状态检查
- **接口地址**: `GET /api/v1/test/health`
- **功能描述**: 检查API服务的健康状态
- **响应格式**:
  ```json
  {
    "status": "success",
    "message": "API v1版本健康状态正常",
    "data": {
      "health": "ok",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  }
  ```

## 使用示例
```python
import requests

# 测试API版本
response = requests.get('http://localhost:5000/api/v1/test')
print(response.json())

# 检查健康状态
response = requests.get('http://localhost:5000/api/v1/test/health')
print(response.json())
```

## 响应状态说明
- `status`: "success" 表示请求成功处理
- `message`: 描述性的状态消息
- `data`: 包含具体的测试结果数据

## 监控建议
1. 定期调用健康检查接口监控服务状态
2. 使用API版本测试接口验证版本兼容性
3. 建议设置监控告警，当健康状态异常时及时处理
# Physical健康对话接口文档

## 接口概述

Physical健康对话接口提供基于Coze Agent的健康咨询服务，支持单轮对话模式。该接口适用于没有知识库支持的场景，每次对话都是独立的请求。

## 接口地址

### 非流式接口
```
POST /health/chat/physical
```

### 流式接口（SSE）
```
POST /health/chat/physical/stream
```

## 请求参数

### 请求头
```
Content-Type: application/json
```

### 请求体
```json
{
  "message": "用户输入的健康相关问题"
}
```

**参数说明：**
- `message` (string, 必填): 用户的健康咨询问题

## 响应格式

### 非流式接口响应

#### 成功响应
```json
{
  "health": {
    "status": "success",
    "message": "Physical chat completed",
    "data": {
      "response": "回答内容...",
      "conversation_id": "会话ID"
    }
  },
  "timestamp": 时间戳
}
```

#### 错误响应
```json
{
  "health": {
    "status": "error",
    "message": "错误描述",
    "data": null
  },
  "timestamp": 时间戳
}
```

### 流式接口响应

流式接口返回SSE格式的数据：
```
data:{"event":"message","message":{...},"is_finish":true,"index":0,"conversation_id":"...","seq_id":0}
```

## 测试方法

### 1. 使用Python脚本测试

```bash
python testCase\test_physical.py
```

### 2. 使用curl命令测试

#### 非流式接口
```bash
curl -X POST http://localhost:5000/health/chat/physical \
  -H "Content-Type: application/json" \
  -d '{"message": "我最近经常感到疲劳，有什么建议吗？"}'
```

#### 流式接口
```bash
curl -X POST http://localhost:5000/health/chat/physical/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "我想了解如何改善睡眠质量？"}'
```

### 3. 使用PowerShell测试

```powershell
# 非流式接口
$body = @{
    message = "我最近经常感到疲劳，有什么建议吗？"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/health/chat/physical" -Method Post -Body $body -ContentType "application/json"

# 流式接口
$body = @{
    message = "我想了解如何改善睡眠质量？"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/health/chat/physical/stream" -Method Post -Body $body -ContentType "application/json"
```

## 客户端调用示例

### JavaScript (前端/Node.js)

#### 非流式调用
```javascript
async function callPhysicalChat(message) {
  try {
    const response = await fetch('http://localhost:5000/health/chat/physical', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    
    const data = await response.json();
    if (data.health.status === 'success') {
      return data.health.data.response;
    } else {
      throw new Error(data.health.message);
    }
  } catch (error) {
    console.error('调用失败:', error);
    throw error;
  }
}

// 使用示例
callPhysicalChat("我最近经常感到疲劳，有什么建议吗？")
  .then(response => console.log(response))
  .catch(error => console.error(error));
```

#### 流式调用
```javascript
function callPhysicalChatStream(message, onMessage, onComplete) {
  const eventSource = new EventSource('http://localhost:5000/health/chat/physical/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });
  
  eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    onMessage(data);
  };
  
  eventSource.onerror = function(event) {
    console.error('流式调用出错:', event);
    eventSource.close();
  };
  
  // 可以通过某种方式在完成后调用
  // eventSource.close();
  // onComplete();
}
```

### Python客户端

```python
import requests
import json

def call_physical_chat(message):
    """调用Physical健康对话接口"""
    url = "http://localhost:5000/health/chat/physical"
    
    payload = {
        "message": message
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        if data.get("health", {}).get("status") == "success":
            return data["health"]["data"]["response"]
        else:
            raise Exception(data.get("health", {}).get("message", "未知错误"))
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {e}")
    except json.JSONDecodeError as e:
        raise Exception(f"响应解析失败: {e}")

# 使用示例
try:
    response = call_physical_chat("我最近经常感到疲劳，有什么建议吗？")
    print(response)
except Exception as e:
    print(f"调用失败: {e}")
```

## 拼接完整结果的方法

### 非流式接口
非流式接口一次性返回完整结果，无需拼接。

### 流式接口
对于流式接口，需要拼接多个数据块来形成完整结果：

```javascript
class PhysicalChatAssembler {
  constructor() {
    this.fullResponse = "";
    this.conversationId = null;
  }
  
  processStreamData(data) {
    // 处理SSE数据块
    if (data.event === "message") {
      const content = data.message.content;
      this.fullResponse += content;
      
      // 保存会话ID
      if (data.conversation_id) {
        this.conversationId = data.conversation_id;
      }
    }
    
    return {
      content: this.fullResponse,
      conversationId: this.conversationId,
      isComplete: data.is_finish
    };
  }
  
  reset() {
    this.fullResponse = "";
    this.conversationId = null;
  }
}

// 使用示例
const assembler = new PhysicalChatAssembler();

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  const result = assembler.processStreamData(data);
  
  // 更新UI显示累积的内容
  updateUI(result.content);
  
  if (result.isComplete) {
    console.log("完整响应:", result.content);
    console.log("会话ID:", result.conversationId);
  }
};
```

## 错误处理

### 常见错误码
- `400`: 请求参数错误
- `500`: 服务器内部错误
- `502`: Coze API调用失败

### 错误处理建议
```javascript
async function callPhysicalChatWithErrorHandling(message) {
  try {
    const response = await fetch('http://localhost:5000/health/chat/physical', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // 检查业务状态
    if (data.health.status === 'success') {
      return data.health.data.response;
    } else if (data.health.status === 'error') {
      throw new Error(data.health.message);
    } else {
      throw new Error('未知响应格式');
    }
  } catch (error) {
    // 根据错误类型提供不同的处理方式
    if (error.name === 'TypeError') {
      // 网络错误
      console.error('网络连接失败，请检查网络设置');
    } else if (error.message.includes('HTTP error')) {
      // HTTP错误
      console.error('服务器错误，请稍后重试');
    } else {
      // 业务错误
      console.error('请求失败:', error.message);
    }
    
    throw error;
  }
}
```

## 注意事项

1. **单轮对话**: 当前接口为单轮对话模式，每次请求都是独立的会话
2. **会话ID**: 每次请求都会生成新的会话ID，不支持多轮对话的上下文保持
3. **响应时间**: 根据网络状况和Coze API响应时间，可能需要几秒到十几秒
4. **错误重试**: 建议在客户端实现适当的错误重试机制
5. **字符编码**: 确保请求和响应都使用UTF-8编码

## 测试脚本

项目提供了多种语言的测试脚本：
- `testCase/test_physical.py` - Python测试脚本
- `testCase/test_physical.ps1` - PowerShell测试脚本
- `testCase/test_physical.js` - Node.js测试脚本

可以直接运行这些脚本来验证接口功能。
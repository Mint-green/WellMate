# well-mate后端项目

这是一个基于Flask的well-mate后端项目，提供了测试接口和健康相关的业务接口。

## 项目结构
```
well-mate-backend/
├── app.py              # 主应用文件，包含路由和蓝图定义
├── requirements.txt    # 项目依赖
├── gunicorn.conf.py    # Gunicorn配置文件
├── .env.example        # 环境变量示例文件
├── test_sse.py         # Python版SSE测试脚本
├── test_sse.js         # JavaScript版SSE测试脚本
├── test_sse.ps1        # PowerShell版SSE测试脚本
├── .gitignore          # Git忽略文件配置
└── README.md           # 项目说明文档
└── api/
    ├── __init__.py     # 蓝图注册
    ├── testapi/
    └── health/
        ├── __init__.py # 健康模块主文件
        ├── chat/
        └── data/
```

## 接口设计

项目使用蓝图(Blueprint)组织不同前缀的接口：

### 测试接口前缀：/testapi
- `GET /testapi/test` - 测试接口，用于验证服务是否正常运行

### 健康数据接口前缀：/health/data
- `POST /health/data/sync` - 同步健康数据接口

### 健康对话接口前缀：/health/chat
- `POST /health/chat/text` - 文本对话接口（非流式版本）
- `POST /health/chat/text/stream` - 文本对话接口（SSE流式版本）

## 环境配置

1. 创建虚拟环境（如果尚未创建）：
```bash
python -m venv .venv
```

2. 激活虚拟环境：
- Windows: 
```bash
.venv\Scripts\activate
```
- macOS/Linux: 
```bash
source .venv/bin/activate
```

3. 复制环境变量示例文件并重命名：
```bash
# Windows
copy .env.example .env
# macOS/Linux
cp .env.example .env
```

4. 根据需要编辑.env文件配置环境变量

5. 安装依赖：
```bash
pip install -r requirements.txt
```

## 运行项目

### 开发环境

```bash
python app.py
```

服务将在 http://localhost:5000 启动，开启调试模式。

### 生产环境

docker打镜像并推送：
powershell: 
```bash
cmd /c build_and_push.bat
```


## 接口测试

可以使用curl、Postman等工具测试接口：

- 测试接口：
```bash
curl http://localhost:5000/testapi/test
```

- 健康数据同步接口：
```bash
curl -X POST http://localhost:5000/health/data/sync
```

- 文本对话接口（非流式）：
```bash
curl -X POST http://localhost:5000/health/chat/text
```

- 文本对话接口（SSE流式）：
使用提供的测试脚本进行测试：
```bash
# Python版本
python test_sse.py

# JavaScript版本
node test_sse.js

# PowerShell版本
powershell -ExecutionPolicy Bypass -File .\test_sse.ps1
```
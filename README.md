# well-mate后端项目

这是一个基于Flask的well-mate后端项目，提供了测试接口和健康相关的业务接口。项目支持完整的CI/CD流程，包含本地构建和服务器部署功能。

## 项目结构
```
well-mate-backend/
├── app.py              # 主应用文件，包含路由和蓝图定义
├── requirements.txt    # 项目依赖
├── gunicorn.conf.py    # Gunicorn配置文件
├── dockerfile          # Docker镜像构建文件
├── .env.example        # 环境变量示例文件
├── .gitignore          # Git忽略文件配置
├── README.md           # 项目说明文档
├── api/                # API接口模块
│   ├── __init__.py     # 蓝图注册
│   ├── testapi/        # 测试接口模块
│   └── health/         # 健康相关接口模块
│       ├── __init__.py # 健康模块主文件
│       ├── chat/       # 健康对话接口
│       └── data/       # 健康数据接口
├── build/              # 本地构建和镜像打包
│   ├── build_and_push.sh      # Linux/macOS构建脚本
│   ├── build_and_push.bat     # Windows构建脚本
│   ├── docker_build.conf      # 构建配置文件
│   ├── docker_build.conf.example  # 配置示例文件
│   ├── read_config.bat        # Windows配置读取脚本
│   ├── read_config.py         # 配置读取Python脚本
│   └── version.info           # 版本信息文件
├── deploy/             # 服务器部署管理
│   ├── deploy.sh               # 部署脚本
│   ├── deploy_manager.sh      # 部署管理脚本
│   ├── docker_acr.conf         # 部署配置文件
│   ├── docker_acr.conf.example # 配置示例文件
│   ├── get_current_version.sh  # 版本查看脚本
│   ├── read_config.py         # 配置读取Python脚本
│   └── repull_latest.sh       # 重新拉取镜像脚本
└── testCase/           # 测试用例
    ├── test_sse.py     # Python版SSE测试脚本
    ├── test_sse.js     # JavaScript版SSE测试脚本
    └── test_sse.ps1    # PowerShell版SSE测试脚本
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

### 环境变量文件说明

项目支持环境变量文件，按以下优先级加载：
1. `.env.local` - 本地调试配置（不提交到仓库，优先级最高）
2. `.env` - 主要环境配置（已提交到仓库，默认为生产环境配置）

#### 环境配置说明

**生产环境配置（.env文件）**：
- 已提交到仓库，默认为生产环境配置
- 本地打包镜像时只加载此文件
- 包含生产环境默认配置

**本地调试配置（.env.local文件）**：
- 不提交到仓库，用于本地开发调试
- 优先级高于.env文件，本地调试时会覆盖生产配置
- 已创建默认的本地调试配置

#### 本地调试步骤

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

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. **使用.env.local进行本地调试**：
- 项目已创建默认的.env.local文件
- 本地运行时会自动优先加载.env.local配置
- 无需修改.env文件，保持生产配置不变

#### 日志配置说明

项目使用Gunicorn的日志系统，**生产环境日志会写入文件**：

- **访问日志**：`logs/access.log` - 记录HTTP请求信息（IP、方法、路径、状态码等）
- **错误日志**：`logs/error.log` - 记录错误和异常信息
- **日志级别**：通过LOG_LEVEL环境变量控制
- **本地调试**：开发模式下仍输出到控制台便于调试

**日志文件管理**：
- logs目录已创建并添加到.gitignore
- 生产环境会自动创建和写入日志文件
- 建议定期清理或轮转日志文件

**Docker容器中日志位置**：
- 容器内路径：`/app/logs/`
- 访问日志：`/app/logs/access.log`
- 错误日志：`/app/logs/error.log`
- 查看日志：`docker logs <container_name>` 或进入容器查看文件

#### SECRET_KEY使用说明

- **当前状态**：项目为纯API服务，暂时不需要SECRET_KEY配置
- **未来扩展**：如果需要添加用户认证、会话管理等功能时，可启用SECRET_KEY配置
- **当前配置**：所有SECRET_KEY相关配置已注释，可根据需要启用

### 构建和部署环境配置

#### build文件夹 - 本地镜像构建

`build/` 文件夹用于本地打包项目并构建Docker镜像，支持两种构建方式：

**Windows环境（使用bat脚本）：**
```bash
cd build
build_and_push.bat
```

**Linux/macOS环境（使用sh脚本）：**
```bash
cd build
./build_and_push.sh
```

**构建配置文件：**
- `docker_build.conf` - 构建配置（包含ACR仓库信息）
- `docker_build.conf.example` - 配置示例文件

**构建功能特性：**
- 自动版本管理（时间戳+序号）
- 智能重试机制（3次重试）
- ACR仓库自动登录和推送
- 详细的错误诊断和网络诊断

#### deploy文件夹 - 服务器部署管理

`deploy/` 文件夹用于在服务器上拉取镜像并进行部署管理：

**部署管理脚本：**
```bash
cd deploy
./deploy_manager.sh
```

**部署功能特性：**
- 统一的部署管理界面
- 支持多种部署操作：
  - 部署最新版本
  - 重新拉取并部署
  - 查看当前版本
  - 容器状态管理
  - 部署日志查看

**部署配置文件：**
- `docker_acr.conf` - 部署配置（包含容器名称和ACR信息）
- `docker_acr.conf.example` - 配置示例文件

## 运行项目

### 开发环境

```bash
python app.py
```

服务将在 http://localhost:5000 启动，开启调试模式。

### 生产环境 - 镜像构建和部署

#### 1. 本地构建镜像（使用build文件夹）

**Windows环境：**
```powershell
cd build
build_and_push.bat
```

**Linux/macOS环境：**
```bash
cd build
./build_and_push.sh
```

**构建过程说明：**
- 自动生成版本标签（格式：YYYYMMDDHHMM + 序号）
- 构建Docker镜像并注入版本信息
- 自动登录阿里云ACR仓库
- 推送镜像到仓库（支持重试机制）

#### 2. 服务器部署（使用deploy文件夹）

**在服务器上执行：**
```bash
cd deploy
./deploy_manager.sh
```

**部署管理功能：**
- 1. 部署最新版本
- 2. 重新拉取并部署
- 3. 查看当前部署版本
- 4. 查看容器状态
- 5. 重启容器
- 6. 停止容器
- 7. 查看部署日志

#### 3. 直接部署（快速方式）

```bash
cd deploy
./deploy.sh
```

直接拉取最新镜像并启动容器。


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
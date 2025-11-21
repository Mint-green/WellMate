# Wellmate 健康助手后端项目

## 项目概述

Wellmate 是一个基于 Flask 的健康助手后端系统，提供专业的身体健康和心理健康咨询服务。项目采用微服务架构，集成外部 AI 智能体服务，支持完整的用户认证、会话管理、健康数据管理和智能对话功能。

### 核心特性

- **🤖 智能健康咨询**：集成专业的身体健康和心理健康 AI 智能体
- **🔐 安全认证**：基于 JWT 的完整用户认证和授权系统
- **💬 智能会话管理**：支持上下文感知的对话管理和历史记录
- **🎯 流式响应**：支持 SSE 流式对话，提供实时交互体验
- **📊 健康数据管理**：完整的健康数据存储和分析功能
- **🐳 容器化部署**：支持 Docker 容器化部署和 CI/CD 流程
- **📱 API 优先**：为移动端应用提供完整的 RESTful API 接口

### 技术栈

- **后端框架**：Flask + Gunicorn
- **数据库**：MySQL 8.0
- **认证系统**：JWT Token 认证
- **会话管理**：自定义会话管理器
- **AI 集成**：Coze 平台智能体服务
- **部署方式**：Docker 容器化部署
- **API 设计**：RESTful API + SSE 流式接口

## 项目结构

```
wellmate-backend/
├── 📄 app.py                          # 主应用文件，路由和蓝图定义
├── 📄 requirements.txt                # Python 依赖包列表
├── 📄 gunicorn.conf.py                # Gunicorn 生产环境配置
├── 📄 dockerfile                      # Docker 镜像构建文件
├── 📄 .env.example                    # 环境变量配置模板
├── 📄 README.md                       # 项目说明文档
├── 📄 architecture_diagram.md         # 系统架构文档
├── 📄 API_DOCUMENTATION.md            # 完整 API 接口文档
├── 📄 version.info                    # 版本信息文件
├── 📁 api/                            # API 接口模块
│   ├── 📄 __init__.py                 # 蓝图注册
│   ├── 📁 docs/                       # API 文档目录
│   └── 📁 v1/                         # API v1 版本
│       ├── 📄 __init__.py             # v1 蓝图注册
│       ├── 📁 auth/                   # 用户认证接口，包含注册、登录、Token刷新等功能
│       ├── 📁 health/                 # 健康管理模块
│       │   ├── 📄 __init__.py         # 健康模块初始化
│       │   ├── 📁 chat/               # 健康对话接口，包含流式和非流式对话功能
│       │   ├── 📁 data/               # 健康数据接口，包含数据获取、添加、统计等功能
│       │   ├── 📁 mental/             # 心理健康接口，提供情绪支持和心理咨询服务
│       │   ├── 📁 physical/           # 身体健康接口，提供身体健康建议和运动饮食推荐
│       │   └── 📁 sessions/           # 会话管理接口，包含会话创建、获取、删除等功能
│       ├── 📁 test/                    # 测试接口，包含健康检查和数据库连接测试
│       └── 📁 users/                  # 用户管理接口，包含用户信息获取和设置更新功能
├── 📁 build/                          # 本地构建和镜像打包脚本
├── 📁 config/                         # 配置模块，包含数据库配置
├── 📁 deploy/                         # 服务器部署管理脚本
├── 📁 deploy_mysql/                   # MySQL 部署配置和初始化脚本
├── 📁 testCase/                       # 测试用例，包含多种语言的测试脚本
└── 📁 utils/                          # 工具模块，包含缓存、数据库连接、JWT认证等工具
```

## 核心功能模块

### 1. 用户认证系统
- **用户注册/登录**：完整的用户注册和登录流程
- **JWT Token 管理**：支持 access token 和 refresh token
- **权限控制**：基于 token 的接口访问控制
- **会话安全**：自动 token 刷新和安全验证

### 2. 健康对话系统
- **身体健康咨询**：专业的身体健康问题解答和建议
- **心理健康支持**：情绪分析和心理支持服务
- **智能会话管理**：自动维护对话上下文和历史记录
- **流式响应**：支持实时流式对话体验

### 3. 会话管理系统
- **会话创建/管理**：自动创建和管理用户会话
- **历史记录存储**：完整的对话历史记录存储
- **上下文感知**：智能维护对话上下文连续性
- **会话恢复**：支持会话中断后的恢复功能

### 4. 健康数据管理
- **数据存储**：用户健康数据的完整存储管理
- **数据分析**：健康数据的统计和分析功能
- **数据同步**：支持多端数据同步和备份
- **隐私保护**：严格的数据访问权限控制

## 快速开始

### 环境要求

- **Python**: 3.8+
- **MySQL**: 8.0+
- **Docker**: 20.10+ (可选，用于容器化部署)
- **操作系统**: Windows/Linux/macOS

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd wellmate-backend
```

2. **创建虚拟环境**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

5. **初始化数据库**
```bash
python scripts/init_database.py
```

6. **启动开发服务器**
```bash
python app.py
```

服务将在 http://localhost:5000 启动

### 生产环境部署

#### Docker 容器化部署

1. **构建 Docker 镜像**
```bash
cd build
# Windows
build_and_push.bat
# Linux/macOS
./build_and_push.sh
```

2. **服务器部署**
```bash
cd deploy
./deploy_manager.sh
```

#### 直接部署

```bash
cd deploy
./deploy.sh
```

## API 接口概览

### 认证接口
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - Token 刷新

### 用户管理接口
- `GET /api/v1/users/profile` - 获取用户信息
- `PUT /api/v1/users/settings` - 更新用户设置

### 健康对话接口
- `POST /api/v1/health/physical/chat` - 身体健康对话（非流式）
- `POST /api/v1/health/physical/chat/stream` - 身体健康对话（流式）
- `POST /api/v1/health/mental/chat` - 心理健康对话（非流式）
- `POST /api/v1/health/mental/chat/stream` - 心理健康对话（流式）

### 会话管理接口
- `GET /api/v1/health/sessions` - 获取会话列表
- `POST /api/v1/health/sessions` - 创建新会话
- `GET /api/v1/health/sessions/{session_id}` - 获取会话详情
- `DELETE /api/v1/health/sessions/{session_id}` - 删除会话

### 健康数据接口
- `GET /api/v1/health/data` - 获取健康数据
- `POST /api/v1/health/data` - 添加健康数据
- `GET /api/v1/health/data/stats` - 获取健康统计

### 测试接口
- `GET /api/v1/test/health` - 健康检查
- `GET /api/v1/test/db` - 数据库连接测试

## 接口使用示例

### 完整登录和对话流程

```bash
# 1. 用户注册
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "full_name": "测试用户",
    "gender": "male",
    "age": 25
  }'

# 2. 用户登录
response=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }')

# 3. 提取 access token
token=$(echo $response | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 4. 身体健康对话
curl -X POST http://localhost:5000/api/v1/health/physical/chat \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我最近经常头痛，应该注意什么？"
  }'
```

### 流式对话示例

```python
import requests

# 流式对话请求
response = requests.post('http://localhost:5000/api/v1/health/mental/chat/stream', 
                       headers={'Authorization': f'Bearer {token}'},
                       json={'text': '如何应对工作压力？'}, 
                       stream=True)

# 处理流式响应
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 数据库设计

### 用户表结构

```sql
CREATE TABLE users (
    uuid VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    gender ENUM('male', 'female', 'other'),
    age INT,
    birth_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 会话和消息表

系统支持完整的会话管理和消息存储功能，包括：
- 会话创建和生命周期管理
- 消息的完整存储和检索
- 对话上下文的智能维护
- 历史记录的自动传递

## 配置说明

### 环境变量配置

项目使用 `.env` 文件管理配置，主要配置项包括：

```bash
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=wellmate

# JWT 配置
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ACCESS_TOKEN_EXPIRES=86400
JWT_REFRESH_TOKEN_EXPIRES=2592000

# AI 服务配置
MENTAL_AGENT_BASE_URL=http://47.113.206.45:6001
PHYSICAL_AGENT_BASE_URL=http://your_physical_agent_url

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
DEBUG=False
```

### 本地开发配置

创建 `.env.local` 文件用于本地开发调试：

```bash
# 本地开发配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=local_password
DEBUG=True
```

## 测试和调试

### 数据库连接测试

```bash
python scripts/test_db_connection.py
```

### Mental Agent 服务测试

```bash
python scripts/test_mental_agent.py
```

### SSE 流式接口测试

```bash
python scripts/test_sse.py
```

### API 诊断测试

```bash
python testCase/diagnose_mental_api.py
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 MySQL 服务是否启动
   - 验证数据库配置信息
   - 运行数据库连接测试脚本

2. **JWT Token 认证失败**
   - 检查 token 是否过期
   - 验证 token 签名和格式
   - 确认 JWT 密钥配置正确

3. **AI 服务连接失败**
   - 检查外部服务地址配置
   - 验证网络连接
   - 运行服务健康检查脚本

### 日志查看

生产环境日志位置：
- 访问日志：`logs/access.log`
- 错误日志：`logs/error.log`
- Docker 容器日志：`docker logs <container_name>`

## 开发指南

### 代码结构规范

- API 接口按功能模块组织在 `api/v1/` 目录下
- 工具函数统一放在 `utils/` 目录
- 脚本文件放在 `scripts/` 目录
- 测试用例放在 `testCase/` 目录

### API 开发规范

- 所有接口使用 RESTful 设计原则
- 请求和响应使用 JSON 格式
- 错误处理使用统一格式
- 接口文档及时更新

### 数据库操作规范

- 使用参数化查询防止 SQL 注入
- 数据库操作进行异常处理
- 重要操作记录操作日志
- 定期备份数据库

## 部署说明

### 构建和部署流程

1. **本地构建**：使用 `build/` 目录下的脚本构建 Docker 镜像
2. **镜像推送**：自动推送到容器镜像仓库
3. **服务器部署**：使用 `deploy/` 目录下的脚本进行部署
4. **健康检查**：自动进行服务健康检查

### 部署管理

使用部署管理脚本进行完整的部署管理：

```bash
cd deploy
./deploy_manager.sh
```

支持的操作包括：
- 部署最新版本
- 重新拉取并部署
- 查看当前版本
- 容器状态管理
- 重启/停止容器
- 查看部署日志

---

**注意**：详细的技术文档和 API 接口说明请参考项目中的 `API_DOCUMENTATION.md` 和各模块的详细文档。
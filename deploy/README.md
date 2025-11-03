# 健康助手后端部署系统

## 概述

本部署系统采用"构建时注入版本信息 + 服务器端拉取latest标签"的方案，避免服务器本地拉取过多镜像，同时确保版本信息可追溯。

## 系统架构

### 构建阶段
- 在构建镜像时注入版本信息（时间戳、标签、镜像ID、Digest等）
- 创建版本信息文件（version.txt）并包含在镜像中
- 同时构建时间戳标签和latest标签的镜像

### 部署阶段
- 服务器端只拉取latest标签的镜像
- 通过镜像内的版本信息文件获取详细的构建信息
- 记录部署信息到本地文件（deploy.info）

## 文件结构

```
deploy/
├── deploy.sh                 # 部署最新版本脚本
├── repull_latest.sh          # 重新拉取并部署脚本
├── get_current_version.sh    # 获取当前版本信息脚本
├── deploy_manager.sh         # 部署管理主脚本
├── docker_acr.conf           # ACR配置信息文件（不提交到Git）
├── docker_acr.conf.example   # 配置模板文件
├── read_config.py            # 配置读取脚本
└── README.md                 # 说明文档
```

## 使用方法

### 1. 使用部署管理主脚本（推荐）

```bash
# 进入部署目录
cd deploy

# 添加执行权限
chmod +x *.sh

# 运行部署管理脚本
./deploy_manager.sh
```

管理脚本提供以下功能：
- 部署最新版本
- 重新拉取并部署最新版本
- 查看当前部署版本
- 查看容器状态
- 重启容器
- 停止容器
- 查看部署日志

### 2. 使用独立脚本

#### 部署最新版本
```bash
./deploy.sh
```

#### 重新拉取并部署
```bash
./repull_latest.sh
```

#### 查看当前版本信息
```bash
./get_current_version.sh
```

## 配置信息

### 配置文件系统

部署系统使用配置文件来管理ACR仓库和容器配置，避免敏感信息硬编码在脚本中。

#### 配置文件结构
```
deploy/
├── docker_acr.conf           # 实际配置文件（不提交到Git）
├── docker_acr.conf.example   # 配置模板文件
└── read_config.py            # 配置读取脚本
```

#### 配置项说明
配置文件采用简单的键值对格式（类似version.info），包含以下配置项：

```conf
# ACR仓库配置
acr_repo=your-acr-repository-url
acr_user=your-acr-username
acr_registry=your-acr-registry-url

# 容器配置
container_name=your-container-name
port=8000
```

#### 使用方法

1. **首次配置**：
   ```bash
   # 复制模板文件
   cp docker_acr.conf.example docker_acr.conf
   
   # 编辑配置文件
   vim docker_acr.conf
   ```

2. **配置内容**：根据实际环境修改以下配置项：
   - `acr_repo`: ACR仓库完整地址
   - `acr_user`: ACR用户名
   - `acr_registry`: ACR注册表地址
   - `container_name`: 容器名称
   - `port`: 服务端口

3. **配置验证**：
   ```bash
   # 测试配置读取
   python read_config.py acr_repo
   python read_config.py container_name
   ```

### ACR仓库配置（示例）
- **仓库地址**: `crpi-t94140ki6zwcf0xb.cn-shenzhen.personal.cr.aliyuncs.com/hku-projects/health-assistant-backend`
- **用户名**: `docker-op@1011858784784063`

### 容器配置（示例）
- **容器名称**: `health-assistant-backend`
- **端口映射**: `8000:8000`
- **重启策略**: `unless-stopped`

### 文件路径
- **版本信息文件**: `/app/version.txt`（容器内）
- **部署信息文件**: `/app/deploy.info`（服务器本地）

## 版本信息

### 构建时注入的信息
- `BUILD_TIMESTAMP`: 构建时间戳（YYYYMMDDHHMM格式）
- `BUILD_TAG`: 构建标签（时间戳+序号）
- `BUILD_DATE`: 构建日期
- `GIT_COMMIT`: Git提交哈希
- `GIT_BRANCH`: Git分支
- `IMAGE_ID`: 镜像ID
- `IMAGE_DIGEST`: 镜像Digest

### 部署时记录的信息
- 部署时间
- 容器ID
- 镜像信息
- 操作类型

## 工作流程

### 构建流程
1. 生成时间戳和序号
2. 创建版本信息文件
3. 构建带版本信息的镜像
4. 推送镜像到ACR仓库

### 部署流程
1. 检查Docker环境
2. 登录ACR仓库（如果需要）
3. 拉取latest标签镜像
4. 检查是否需要更新
5. 停止旧容器（如果存在）
6. 启动新容器
7. 记录部署信息

## 注意事项

1. **权限设置**: 首次使用前需要为脚本添加执行权限
   ```bash
   chmod +x deploy/*.sh
   ```

2. **ACR登录**: 首次部署或登录过期时需要输入ACR密码

3. **镜像清理**: 系统会自动保留最近3个版本的镜像，清理旧镜像

4. **版本验证**: 部署时会验证镜像ID，确保部署的是正确的版本

5. **错误处理**: 所有脚本都包含错误处理和状态检查

## 故障排除

### 常见问题

1. **Docker未安装或未启动**
   ```bash
   # 检查Docker状态
   systemctl status docker
   
   # 启动Docker服务
   systemctl start docker
   ```

2. **ACR登录失败**
   - 检查用户名是否正确
   - 确认密码是否有权限
   - 尝试手动登录：`docker login crpi-t94140ki6zwcf0xb.cn-shenzhen.personal.cr.aliyuncs.com`

3. **端口冲突**
   - 检查8000端口是否被占用
   - 可以修改脚本中的端口配置

4. **容器启动失败**
   - 查看容器日志：`docker logs health-assistant-backend`
   - 检查镜像是否存在：`docker images`

### 日志查看

```bash
# 查看容器日志
./deploy_manager.sh  # 选择7查看日志

# 或直接使用Docker命令
docker logs health-assistant-backend

# 查看最近50行日志
docker logs --tail 50 health-assistant-backend
```

## 扩展功能

系统支持以下扩展功能：

1. **健康检查**: 可以添加健康检查端点验证服务状态
2. **监控集成**: 可以集成Prometheus等监控系统
3. **回滚功能**: 基于版本信息实现快速回滚
4. **多环境部署**: 支持开发、测试、生产等多环境部署

## 联系方式

如有问题请联系系统管理员。
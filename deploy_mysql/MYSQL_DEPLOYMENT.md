# MySQL容器化部署方案

## 概述

本文档提供MySQL数据库的Docker容器化部署方案，支持开发、测试和生产环境的快速部署。

## 目录结构

```
deploy_mysql/
├── mysql.conf              # MySQL配置文件
├── init_mysql.sh           # MySQL容器初始化脚本
├── mysql_manager.sh        # MySQL容器管理脚本
├── mysql_data/             # MySQL数据持久化目录
├── mysql_config/           # MySQL配置文件目录
├── init_sql/               # 数据库初始化脚本目录
│   ├── 01_create_users_table.sql    # 用户表创建脚本
│   └── 02_insert_test_users.sql     # 测试用户数据脚本
└── backups/                # 数据库备份目录
```

## 快速开始

### 1. 环境准备
确保系统已安装Docker和Docker Compose。

### 2. 配置修改
编辑 `mysql.conf` 文件，根据实际环境修改配置：

```bash
# 修改默认密码（生产环境必须修改）
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_USER=your_username
MYSQL_PASSWORD=your_secure_password

# 修改数据持久化路径（可选）
DATA_VOLUME_PATH=/path/to/your/mysql_data
```

### 3. 初始化部署
```bash
# 给脚本添加执行权限
chmod +x init_mysql.sh mysql_manager.sh

# 初始化并启动MySQL容器
./init_mysql.sh
```

### 4. 验证部署
```bash
# 检查容器状态
./mysql_manager.sh status

# 查看容器日志
./mysql_manager.sh logs
```

## 配置说明

### mysql.conf 配置文件

```bash
# Docker相关配置
MYSQL_IMAGE=mysql:8.0           # MySQL镜像版本
CONTAINER_NAME=wellmate_mysql  # 容器名称
NETWORK_NAME=wellmate_network  # Docker网络名称

# MySQL配置 (生产环境必须修改密码)
MYSQL_ROOT_PASSWORD=your_secure_root_password_here  # root用户密码
MYSQL_DATABASE=wellmate    # 默认创建的数据库名
MYSQL_USER=wellmateuser             # 普通用户用户名
MYSQL_PASSWORD=your_secure_user_password_here         # 普通用户密码

# 端口映射 (宿主机端口:容器端口)
HOST_PORT=3306
CONTAINER_PORT=3306

# 数据持久化路径 (请根据实际环境修改)
DATA_VOLUME_PATH=./mysql_data
CONFIG_VOLUME_PATH=./mysql_config

# 初始化脚本路径
INIT_SQL_PATH=./init_sql
```

## 容器管理

### 基本操作
```bash
# 启动容器
./mysql_manager.sh start

# 停止容器
./mysql_manager.sh stop

# 重启容器
./mysql_manager.sh restart

# 查看容器状态
./mysql_manager.sh status

# 查看容器日志
./mysql_manager.sh logs

# 删除容器（保留数据）
./mysql_manager.sh remove
```

### 数据管理
```bash
# 备份数据库
./mysql_manager.sh backup

# 恢复数据库
./mysql_manager.sh restore

# 进入MySQL命令行
./mysql_manager.sh shell
```

## 数据库初始化脚本

### init_sql目录说明
- **01_create_users_table.sql**: 创建用户表结构
- **02_insert_test_users.sql**: 插入测试用户数据

### 初始化脚本执行机制

#### 自动执行机制
当MySQL容器首次启动时，会自动执行 `init_sql/` 目录下的所有SQL脚本：

1. **执行顺序**：按文件名数字顺序执行（01_*.sql → 02_*.sql → ...）
2. **执行时机**：仅在容器首次启动时执行，后续重启不会重复执行
3. **执行方式**：通过Docker的 `/docker-entrypoint-initdb.d` 目录自动执行

#### 手动执行SQL脚本
如需手动执行SQL脚本：

```bash
# 方法1：使用mysql_manager.sh的shell功能
./mysql_manager.sh shell

# 在MySQL命令行中执行SQL文件
mysql> source /docker-entrypoint-initdb.d/01_create_users_table.sql;

# 方法2：直接使用docker exec
./mysql_manager.sh shell < /path/to/your_script.sql

# 方法3：进入容器后执行
docker exec -it wellmate_mysql bash
mysql -u wellmateuser -p wellmate < /docker-entrypoint-initdb.d/01_create_users_table.sql
```

### 自定义初始化
如需添加自定义初始化脚本：
1. 将SQL文件放入 `init_sql/` 目录
2. 文件名按数字顺序命名（如03_*.sql）
3. 重启容器：`./mysql_manager.sh restart`

### 查看初始化状态
```bash
# 查看已执行的初始化脚本
./mysql_manager.sh shell -e "SHOW TABLES;"

# 查看用户表结构
./mysql_manager.sh shell -e "DESCRIBE users;"

# 查看测试用户数据
./mysql_manager.sh shell -e "SELECT * FROM users;"
```

## 应用程序连接

### Python连接示例
```python
import mysql.connector

config = {
    'user': 'wellmateuser',
    'password': 'your_secure_user_password_here',  # 请替换为实际密码
    'host': 'localhost',
    'port': 3306,
    'database': 'wellmate',
    'raise_on_warnings': True
}

cnx = mysql.connector.connect(**config)
```

### 连接字符串格式
```
mysql://wellmateuser:your_secure_user_password_here@localhost:3306/wellmate
```

## 数据迁移

### 从现有数据库迁移
1. 导出现有数据：
```bash
mysqldump -u [用户名] -p[密码] -h [主机] [数据库名] > backup.sql
```

2. 将备份文件放入初始化目录：
```bash
cp backup.sql deploy_mysql/init_sql/
```

3. 重新初始化容器：
```bash
./mysql_manager.sh remove
./init_mysql.sh
```

### 容器间数据迁移
```bash
# 备份数据
./mysql_manager.sh backup

# 在新环境中恢复数据
./mysql_manager.sh restore
```

## 性能优化

### MySQL配置文件优化

在 `mysql_config/` 目录中创建 `my.cnf` 文件：

```ini
[mysqld]
# 基本设置
default-storage-engine = InnoDB
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 连接设置
max_connections = 200
max_connect_errors = 10

# InnoDB设置
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# 查询缓存
query_cache_type = 1
query_cache_size = 128M

# 日志设置
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# 其他优化
tmp_table_size = 256M
max_heap_table_size = 256M
table_open_cache = 4096
```

### 容器资源限制
在 `init_mysql.sh` 中可添加资源限制：
```bash
--memory=2g --cpus=2
```

## 安全建议

### 1. 密码安全
- 生产环境必须修改默认密码
- 使用强密码策略
- 定期更换密码

### 2. 网络安全
- 不要将MySQL端口暴露在公网
- 使用Docker网络隔离容器通信
- 定期更新MySQL镜像

### 3. 数据安全
- 定期执行数据库备份
- 备份文件存储在安全位置
- 定期测试备份文件可用性

## 故障排除

### 容器无法启动
```bash
# 检查日志
./mysql_manager.sh logs

# 常见原因：
# - 端口被占用（修改HOST_PORT）
# - 数据目录权限问题
# - 配置文件错误
```

### 连接被拒绝
- 检查MySQL服务是否运行
- 验证端口映射配置
- 检查防火墙设置

### 权限问题
- 确保数据目录读写权限正确
- 验证配置文件中的用户名密码
- 确认用户具有数据库权限

### 常见问题

1. **容器启动失败**
   - 检查端口是否被占用：`netstat -tulpn | grep 3306`
   - 检查Docker服务状态：`systemctl status docker`
   - 查看容器日志：`docker logs wellmate_mysql`

2. **连接数据库失败**
   - 检查MySQL服务是否启动：`docker exec wellmate_mysql mysqladmin ping`
   - 验证连接信息：用户名、密码、端口是否正确
   - 检查防火墙设置：确保3306端口可访问

3. **数据持久化问题**
   - 检查数据卷挂载：`docker inspect wellmate_mysql`
   - 验证目录权限：确保宿主机目录有读写权限
   - 检查磁盘空间：`df -h`

4. **脚本执行错误（Windows/Linux换行符问题）**
   - 问题：Windows创建的配置文件包含CRLF换行符(`\r\n`)，Linux的`source`命令无法正确解析
   - 解决方案：脚本已更新为使用兼容的配置加载方法
   - 验证修复：运行`./init_mysql.sh`或`./mysql_manager.sh status`测试配置加载

## 监控维护

### 监控脚本示例
创建 `monitor_mysql.sh`：
```bash
#!/bin/bash
CONTAINER_NAME="wellmate_mysql"

if docker ps | grep -q $CONTAINER_NAME; then
    echo "[$(date)] MySQL容器运行正常"
else
    echo "[$(date)] MySQL容器异常，尝试重启..."
    ./mysql_manager.sh start
fi
```

### 定时监控
添加到crontab：
```bash
# 每5分钟检查一次
*/5 * * * * /path/to/deploy_mysql/monitor_mysql.sh >> /path/to/monitor.log 2>&1
```

## 版本升级

### 升级步骤
1. 备份数据：`./mysql_manager.sh backup`
2. 修改镜像版本：`MYSQL_IMAGE=mysql:8.1`
3. 重新初始化：`./mysql_manager.sh remove && ./init_mysql.sh`
4. 恢复数据：`./mysql_manager.sh restore`

## 注意事项

1. **数据持久化**：确保 `mysql_data` 目录有足够磁盘空间
2. **备份策略**：建立定期备份机制
3. **安全配置**：生产环境必须修改默认密码
4. **资源限制**：根据需求调整容器资源
5. **日志管理**：定期清理日志文件

## 常见问题

### Q: 如何重置数据库？
A: 删除数据目录并重新初始化：
```bash
rm -rf mysql_data/
./init_mysql.sh
```

### Q: 如何查看数据库表？
A: 进入容器使用MySQL客户端：
```bash
docker exec -it wellmate_mysql mysql -u wellmateuser -p wellmate
```

### Q: 如何执行自定义SQL？
A: 将SQL脚本放入 `init_sql` 目录后重启：
```bash
cp your_script.sql init_sql/
./mysql_manager.sh restart
```

## 与scripts目录的关系

### 功能对比
| 目录 | 用途 | 使用场景 |
|------|------|----------|
| `deploy_mysql/` | Docker容器化部署 | 生产环境部署、Docker环境 |
| `scripts/` | Python脚本管理 | 开发测试、Python应用集成 |

### 推荐使用场景
- **开发阶段**：使用 `scripts/` 目录下的Python脚本
- **部署阶段**：使用 `deploy_mysql/` 目录下的Docker方案

### 数据一致性
两个目录中的数据库表结构定义保持一致，确保数据在不同环境间的兼容性。
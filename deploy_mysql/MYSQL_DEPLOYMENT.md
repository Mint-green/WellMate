# MySQL容器化部署方案

## 目录结构

```
deploy_mysql/
├── mysql.conf              # MySQL配置文件
├── init_mysql.sh           # MySQL容器初始化脚本
├── mysql_manager.sh        # MySQL容器管理脚本
├── mysql_data/             # MySQL数据持久化目录
├── mysql_config/           # MySQL配置文件目录
├── init_sql/               # 数据库初始化脚本目录
└── backups/                # 数据库备份目录
```

## 配置说明

### mysql.conf 配置文件

```bash
# Docker相关配置
MYSQL_IMAGE=mysql:8.0           # MySQL镜像版本
CONTAINER_NAME=wellmate_mysql  # 容器名称
NETWORK_NAME=wellmate_network  # Docker网络名称

# MySQL配置
MYSQL_ROOT_PASSWORD=rootpassword  # root用户密码
MYSQL_DATABASE=wellmate    # 默认创建的数据库名
MYSQL_USER=wellmateuser             # 普通用户用户名
MYSQL_PASSWORD=wellmatepass         # 普通用户密码

# 端口映射 (宿主机端口:容器端口)
HOST_PORT=3306
CONTAINER_PORT=3306

# 数据持久化路径 (请根据实际环境修改)
DATA_VOLUME_PATH=./mysql_data
CONFIG_VOLUME_PATH=./mysql_config

# 初始化脚本路径
INIT_SQL_PATH=./init_sql
```

## 使用方法

### 1. 初始化MySQL容器

```bash
# 给脚本添加执行权限
chmod +x init_mysql.sh
chmod +x mysql_manager.sh

# 初始化并启动MySQL容器
./init_mysql.sh
```

### 2. 管理MySQL容器

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

# 删除容器
./mysql_manager.sh remove

# 备份数据库
./mysql_manager.sh backup

# 恢复数据库
./mysql_manager.sh restore
```

## 数据库连接配置

### 应用程序连接配置

在应用程序中，使用以下配置连接到MySQL数据库：

```python
# Python示例
import mysql.connector

config = {
    'user': 'wellmateuser',
    'password': 'wellmatepass',
    'host': 'localhost',
    'port': 3306,
    'database': 'wellmate',
    'raise_on_warnings': True
}

cnx = mysql.connector.connect(**config)
```

### 连接字符串格式

```
mysql://wellmateuser:wellmatepass@localhost:3306/wellmate
```

## 数据迁移指导

### 1. 从现有数据库迁移

#### 导出现有数据
```bash
# 使用mysqldump导出数据
mysqldump -u [用户名] -p[密码] -h [主机] [数据库名] > backup.sql
```

#### 将备份文件放入初始化目录
```bash
# 将备份文件复制到init_sql目录
cp backup.sql deploy_mysql/init_sql/
```

#### 重新初始化容器
```bash
# 停止并删除现有容器
./mysql_manager.sh remove

# 重新初始化（新容器启动时会自动执行init_sql中的脚本）
./init_mysql.sh
```

### 2. 容器间数据迁移

#### 备份数据
```bash
# 使用管理脚本备份数据
./mysql_manager.sh backup
```

#### 恢复数据到新容器
```bash
# 在新环境中初始化容器后，使用备份文件恢复
./mysql_manager.sh restore
```

## 性能优化配置

### MySQL配置文件

在 `mysql_config/` 目录中创建 `my.cnf` 文件以优化MySQL性能：

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

## 安全建议

### 1. 修改默认密码
在生产环境中，请务必修改 `mysql.conf` 中的默认密码：
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_USER`
- `MYSQL_PASSWORD`

### 2. 网络安全
- 不要将MySQL端口暴露在公网
- 使用Docker网络隔离容器通信
- 定期更新MySQL镜像

### 3. 数据备份
- 定期执行数据库备份
- 将备份文件存储在安全的位置
- 定期测试备份文件的可用性

## 故障排除

### 1. 容器无法启动

检查日志：
```bash
./mysql_manager.sh logs
```

常见原因：
- 端口被占用
- 数据目录权限问题
- 配置文件错误

### 2. 连接被拒绝

检查：
- MySQL服务是否正在运行
- 端口映射是否正确
- 防火墙设置

### 3. 权限问题

确保：
- 数据目录具有正确的读写权限
- 配置文件中的用户名和密码正确
- 用户具有相应的数据库权限

## 监控和维护

### 1. 监控脚本示例

创建监控脚本 `monitor_mysql.sh`：

```bash
#!/bin/bash

CONTAINER_NAME="wellmate_mysql"

# 检查容器状态
if docker ps | grep -q $CONTAINER_NAME; then
    echo "[$(date)] MySQL容器运行正常"
else
    echo "[$(date)] MySQL容器异常，尝试重启..."
    ./mysql_manager.sh start
fi
```

### 2. 定时任务设置

添加到 crontab 实现定期监控：

```bash
# 每5分钟检查一次MySQL状态
*/5 * * * * /path/to/deploy_mysql/monitor_mysql.sh >> /path/to/deploy_mysql/monitor.log 2>&1
```

## 版本升级

### 1. MySQL版本升级步骤

1. 备份现有数据：
```bash
./mysql_manager.sh backup
```

2. 修改配置文件中的镜像版本：
```bash
# 在mysql.conf中修改
MYSQL_IMAGE=mysql:8.1
```

3. 重新初始化容器：
```bash
./mysql_manager.sh remove
./init_mysql.sh
```

4. 恢复数据：
```bash
./mysql_manager.sh restore
```

## 注意事项

1. **数据持久化**：确保 `mysql_data` 目录有足够磁盘空间
2. **备份策略**：建立定期备份机制，避免数据丢失
3. **安全配置**：生产环境中务必修改默认密码
4. **资源限制**：根据实际需求调整容器资源限制
5. **日志管理**：定期清理日志文件，避免磁盘空间不足

## 常见问题

### Q: 如何重置数据库？
A: 删除数据目录并重新初始化容器：
```bash
rm -rf mysql_data/
./init_mysql.sh
```

### Q: 如何查看数据库中的表？
A: 进入容器并使用MySQL客户端：
```bash
docker exec -it wellmate_mysql mysql -u wellmateuser -p wellmate
```

### Q: 如何执行自定义SQL脚本？
A: 将SQL脚本放入 `init_sql` 目录，然后重启容器：
```bash
cp your_script.sql init_sql/
./mysql_manager.sh restart
```
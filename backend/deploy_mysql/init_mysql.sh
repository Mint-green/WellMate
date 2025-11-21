#!/bin/bash

# MySQL容器初始化脚本
# 用于部署和启动MySQL容器服务

set -e  # 遇到错误时退出

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 读取配置信息（使用Python脚本，兼容Windows/Linux）
read_config() {
    local key=$1
    python "${SCRIPT_DIR}/read_mysql_config.py" "$key" 2>/dev/null
}

# 获取配置值
MYSQL_IMAGE=$(read_config "MYSQL_IMAGE")
CONTAINER_NAME=$(read_config "CONTAINER_NAME")
NETWORK_NAME=$(read_config "NETWORK_NAME")
MYSQL_ROOT_PASSWORD=$(read_config "MYSQL_ROOT_PASSWORD")
MYSQL_DATABASE=$(read_config "MYSQL_DATABASE")
MYSQL_USER=$(read_config "MYSQL_USER")
MYSQL_PASSWORD=$(read_config "MYSQL_PASSWORD")
HOST_PORT=$(read_config "HOST_PORT")
CONTAINER_PORT=$(read_config "CONTAINER_PORT")
DATA_VOLUME_PATH=$(read_config "DATA_VOLUME_PATH")
CONFIG_VOLUME_PATH=$(read_config "CONFIG_VOLUME_PATH")
INIT_SQL_PATH=$(read_config "INIT_SQL_PATH")

# 获取可选配置值（内存限制）
CONTAINER_MEMORY_LIMIT=$(read_config "CONTAINER_MEMORY_LIMIT")
CONTAINER_MEMORY_SWAP=$(read_config "CONTAINER_MEMORY_SWAP")
MYSQL_CONFIG_FILE=$(read_config "MYSQL_CONFIG_FILE")

# 设置默认值（如果配置文件中没有设置）
CONTAINER_MEMORY_LIMIT=${CONTAINER_MEMORY_LIMIT:-512m}
CONTAINER_MEMORY_SWAP=${CONTAINER_MEMORY_SWAP:-1g}
MYSQL_CONFIG_FILE=${MYSQL_CONFIG_FILE:-./mysql_config/my.cnf}

# 验证配置是否成功读取
if [ -z "$MYSQL_IMAGE" ] || [ -z "$CONTAINER_NAME" ] || [ -z "$NETWORK_NAME" ] || \
   [ -z "$MYSQL_ROOT_PASSWORD" ] || [ -z "$MYSQL_DATABASE" ] || [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ] || \
   [ -z "$HOST_PORT" ] || [ -z "$CONTAINER_PORT" ] || [ -z "$DATA_VOLUME_PATH" ] || \
   [ -z "$CONFIG_VOLUME_PATH" ] || [ -z "$INIT_SQL_PATH" ]; then
    echo "错误：无法读取配置文件或配置信息不完整。"
    echo "请检查 ${SCRIPT_DIR}/mysql.conf 文件是否存在且格式正确。"
    exit 1
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p $DATA_VOLUME_PATH
mkdir -p $CONFIG_VOLUME_PATH
mkdir -p $INIT_SQL_PATH

# 创建Docker网络（如果不存在）
echo "检查Docker网络..."
if ! docker network ls | grep -q $NETWORK_NAME; then
    echo "创建Docker网络: $NETWORK_NAME"
    docker network create $NETWORK_NAME
else
    echo "Docker网络 $NETWORK_NAME 已存在"
fi

# 检查容器是否已在运行
if docker ps | grep -q $CONTAINER_NAME; then
    echo "MySQL容器 $CONTAINER_NAME 已在运行"
    exit 0
fi

# 检查是否存在已停止的同名容器
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "发现已存在的容器 $CONTAINER_NAME，正在删除..."
    docker rm $CONTAINER_NAME
fi

# 启动MySQL容器
echo "启动MySQL容器..."
docker run -d \
  --name $CONTAINER_NAME \
  --network $NETWORK_NAME \
  --memory=$CONTAINER_MEMORY_LIMIT \
  --memory-swap=$CONTAINER_MEMORY_SWAP \
  -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
  -e MYSQL_DATABASE=$MYSQL_DATABASE \
  -e MYSQL_USER=$MYSQL_USER \
  -e MYSQL_PASSWORD=$MYSQL_PASSWORD \
  -v $DATA_VOLUME_PATH:/var/lib/mysql \
  -v $CONFIG_VOLUME_PATH:/etc/mysql/conf.d \
  -v $INIT_SQL_PATH:/docker-entrypoint-initdb.d \
  -v $MYSQL_CONFIG_FILE:/etc/mysql/my.cnf \
  -p $HOST_PORT:$CONTAINER_PORT \
  $MYSQL_IMAGE

echo "MySQL容器启动命令已执行"

# 等待MySQL服务启动
echo "等待MySQL服务启动..."
for i in {1..30}; do
    if docker exec $CONTAINER_NAME mysqladmin ping --silent; then
        echo "MySQL服务已成功启动"
        break
    fi
    echo "等待MySQL服务启动... ($i/30)"
    sleep 2
done

# 显示容器状态
echo "MySQL容器状态："
docker ps -f name=$CONTAINER_NAME

echo "MySQL容器初始化完成"
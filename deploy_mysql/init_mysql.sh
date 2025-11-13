#!/bin/bash

# MySQL容器初始化脚本
# 用于部署和启动MySQL容器服务

set -e  # 遇到错误时退出

# 配置文件路径
CONFIG_FILE="./mysql.conf"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 配置文件 $CONFIG_FILE 不存在"
    exit 1
fi

# 导入配置
source $CONFIG_FILE

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
  -e MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD \
  -e MYSQL_DATABASE=$MYSQL_DATABASE \
  -e MYSQL_USER=$MYSQL_USER \
  -e MYSQL_PASSWORD=$MYSQL_PASSWORD \
  -v $DATA_VOLUME_PATH:/var/lib/mysql \
  -v $CONFIG_VOLUME_PATH:/etc/mysql/conf.d \
  -v $INIT_SQL_PATH:/docker-entrypoint-initdb.d \
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
    echo "等待MySQL服务启动中... ($i/30)"
    sleep 2
done

# 显示容器状态
echo "MySQL容器状态:"
docker ps -f name=$CONTAINER_NAME

echo "MySQL容器初始化完成"
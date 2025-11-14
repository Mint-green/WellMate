#!/bin/bash

# MySQL容器管理脚本
# 用于管理MySQL容器的启动、停止、重启、状态查看等操作

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

# 验证配置是否成功读取
if [ -z "$MYSQL_IMAGE" ] || [ -z "$CONTAINER_NAME" ] || [ -z "$NETWORK_NAME" ] || \
   [ -z "$MYSQL_ROOT_PASSWORD" ] || [ -z "$MYSQL_DATABASE" ] || [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ] || \
   [ -z "$HOST_PORT" ] || [ -z "$CONTAINER_PORT" ] || [ -z "$DATA_VOLUME_PATH" ] || \
   [ -z "$CONFIG_VOLUME_PATH" ] || [ -z "$INIT_SQL_PATH" ]; then
    echo "错误：无法读取配置文件或配置信息不完整。"
    echo "请检查 ${SCRIPT_DIR}/mysql.conf 文件是否存在且格式正确。"
    exit 1
fi

# 显示帮助信息
show_help() {
    echo "MySQL容器管理脚本"
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     启动MySQL容器"
    echo "  stop      停止MySQL容器"
    echo "  restart   重启MySQL容器"
    echo "  status    查看MySQL容器状态"
    echo "  logs      查看MySQL容器日志"
    echo "  remove    删除MySQL容器"
    echo "  backup    备份MySQL数据库"
    echo "  restore   恢复MySQL数据库"
    echo "  help      显示此帮助信息"
    echo ""
}

# 启动MySQL容器
start_container() {
    echo "启动MySQL容器..."
    
    # 检查容器是否已在运行
    if docker ps | grep -q $CONTAINER_NAME; then
        echo "MySQL容器 $CONTAINER_NAME 已在运行"
        return 0
    fi
    
    # 检查是否存在已停止的同名容器
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo "启动已存在的容器 $CONTAINER_NAME..."
        docker start $CONTAINER_NAME
    else
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
        
        # 启动新的MySQL容器
        echo "启动新的MySQL容器..."
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
    fi
    
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
    
    echo "MySQL容器启动完成"
}

# 停止MySQL容器
stop_container() {
    echo "停止MySQL容器..."
    
    if docker ps | grep -q $CONTAINER_NAME; then
        docker stop $CONTAINER_NAME
        echo "MySQL容器已停止"
    else
        echo "MySQL容器未在运行"
    fi
}

# 重启MySQL容器
restart_container() {
    echo "重启MySQL容器..."
    stop_container
    sleep 2
    start_container
}

# 查看MySQL容器状态
check_status() {
    echo "MySQL容器状态："
    
    # 检查容器是否存在
    if docker ps -a | grep -q $CONTAINER_NAME; then
        # 获取容器状态
        STATUS=$(docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Status}}")
        echo "容器名称: $CONTAINER_NAME"
        echo "容器状态: $STATUS"
        
        # 如果容器正在运行，显示更多详细信息
        if docker ps | grep -q $CONTAINER_NAME; then
            echo "端口映射: $HOST_PORT->$CONTAINER_PORT"
            echo "数据卷挂载："
            echo "  - 数据: $DATA_VOLUME_PATH:/var/lib/mysql"
            echo "  - 配置: $CONFIG_VOLUME_PATH:/etc/mysql/conf.d"
            echo "  - 初始化脚本: $INIT_SQL_PATH:/docker-entrypoint-initdb.d"
        fi
    else
        echo "容器 $CONTAINER_NAME 不存在"
    fi
}

# 查看MySQL容器日志
view_logs() {
    echo "MySQL容器日志："
    
    if docker ps -a | grep -q $CONTAINER_NAME; then
        docker logs $CONTAINER_NAME
    else
        echo "容器 $CONTAINER_NAME 不存在"
    fi
}

# 删除MySQL容器
remove_container() {
    echo "删除MySQL容器..."
    
    # 先停止容器（如果正在运行）
    if docker ps | grep -q $CONTAINER_NAME; then
        docker stop $CONTAINER_NAME
    fi
    
    # 删除容器
    if docker ps -a | grep -q $CONTAINER_NAME; then
        docker rm $CONTAINER_NAME
        echo "MySQL容器已删除"
    else
        echo "容器 $CONTAINER_NAME 不存在"
    fi
}

# 备份MySQL数据库
backup_database() {
    echo "备份MySQL数据库..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="backup_${TIMESTAMP}.sql"
    
    if docker ps | grep -q $CONTAINER_NAME; then
        # 创建备份目录
        mkdir -p ./backups
        
        # 执行备份
        docker exec $CONTAINER_NAME mysqldump -u root -p$MYSQL_ROOT_PASSWORD --all-databases > ./backups/$BACKUP_FILE
        echo "数据库备份完成: ./backups/$BACKUP_FILE"
    else
        echo "MySQL容器未在运行，无法执行备份"
    fi
}

# 恢复MySQL数据库
restore_database() {
    echo "恢复MySQL数据库..."
    echo "请提供备份文件路径:"
    read BACKUP_FILE
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "错误: 备份文件 $BACKUP_FILE 不存在"
        return 1
    fi
    
    if docker ps | grep -q $CONTAINER_NAME; then
        # 执行恢复
        docker exec -i $CONTAINER_NAME mysql -u root -p$MYSQL_ROOT_PASSWORD < $BACKUP_FILE
        echo "数据库恢复完成"
    else
        echo "MySQL容器未在运行，无法执行恢复"
    fi
}

# 主程序逻辑
case "$1" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    status)
        check_status
        ;;
    logs)
        view_logs
        ;;
    remove)
        remove_container
        ;;
    backup)
        backup_database
        ;;
    restore)
        restore_database
        ;;
    help|"")
        show_help
        ;;
    *)
        echo "未知选项: $1"
        show_help
        exit 1
        ;;
esac
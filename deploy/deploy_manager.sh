#!/bin/bash

# 部署管理主脚本
# 提供统一的部署管理界面

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 读取配置信息
read_config() {
    local key=$1
    python3 "${SCRIPT_DIR}/read_config.py" "$key" 2>/dev/null
}

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示菜单函数
show_menu() {
    echo ""
    echo "===================================================="
    echo "          well-mate后端部署管理系统"
    echo "===================================================="
    echo -e "${GREEN}1.${NC} 部署最新版本"
    echo -e "${GREEN}2.${NC} 重新拉取并部署最新版本"
    echo -e "${GREEN}3.${NC} 查看当前部署版本"
    echo -e "${GREEN}4.${NC} 查看容器状态"
    echo -e "${GREEN}5.${NC} 重启容器"
    echo -e "${GREEN}6.${NC} 停止容器"
    echo -e "${GREEN}7.${NC} 查看部署日志"
    echo -e "${GREEN}0.${NC} 退出"
    echo "===================================================="
    echo -n "请选择操作 [0-7]: "
}

# 检查Docker函数
check_docker() {
    docker --version >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误：未安装Docker或Docker服务未启动。${NC}"
        return 1
    fi
    return 0
}

# 部署最新版本
deploy_latest() {
    echo -e "${BLUE}执行部署最新版本...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    bash "${SCRIPT_DIR}/deploy.sh"
}

# 重新拉取并部署
repull_and_deploy() {
    echo -e "${BLUE}执行重新拉取并部署...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    bash "${SCRIPT_DIR}/repull_latest.sh"
}

# 查看当前版本
view_current_version() {
    echo -e "${BLUE}查看当前部署版本...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    bash "${SCRIPT_DIR}/get_current_version.sh"
}

# 查看容器状态
view_container_status() {
    echo -e "${BLUE}查看容器状态...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    # 读取容器名称配置
    CONTAINER_NAME=$(read_config "container_name")
    if [ -z "${CONTAINER_NAME}" ]; then
        echo -e "${RED}错误：无法读取容器名称配置。${NC}"
        return 1
    fi
    
    echo ""
    echo "===================================================="
    echo "容器状态信息"
    echo "===================================================="
    
    # 检查运行中的容器
    RUNNING_CONTAINER=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}" --filter "name=${CONTAINER_NAME}")
    if [ -n "${RUNNING_CONTAINER}" ]; then
        echo -e "${GREEN}运行中的容器：${NC}"
        echo "${RUNNING_CONTAINER}"
    else
        echo -e "${YELLOW}没有运行中的容器。${NC}"
    fi
    
    echo ""
    
    # 检查所有容器（包括停止的）
    ALL_CONTAINERS=$(docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" --filter "name=${CONTAINER_NAME}")
    if [ -n "${ALL_CONTAINERS}" ]; then
        echo -e "${BLUE}所有相关容器：${NC}"
        echo "${ALL_CONTAINERS}"
    fi
    
    echo ""
    echo "===================================================="
}

# 重启容器
restart_container() {
    echo -e "${BLUE}重启容器...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    # 读取容器名称配置
    CONTAINER_NAME=$(read_config "container_name")
    if [ -z "${CONTAINER_NAME}" ]; then
        echo -e "${RED}错误：无法读取容器名称配置。${NC}"
        return 1
    fi
    
    CURRENT_CONTAINER=$(docker ps -q --filter "name=${CONTAINER_NAME}")
    
    if [ -z "${CURRENT_CONTAINER}" ]; then
        echo -e "${YELLOW}没有运行中的容器，尝试启动...${NC}"
        deploy_latest
        return $?
    fi
    
    echo "重启容器：${CURRENT_CONTAINER}"
    docker restart "${CURRENT_CONTAINER}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}容器重启成功。${NC}"
        sleep 3
        view_container_status
    else
        echo -e "${RED}容器重启失败。${NC}"
    fi
}

# 停止容器
stop_container() {
    echo -e "${BLUE}停止容器...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    # 读取容器名称配置
    CONTAINER_NAME=$(read_config "container_name")
    if [ -z "${CONTAINER_NAME}" ]; then
        echo -e "${RED}错误：无法读取容器名称配置。${NC}"
        return 1
    fi
    
    CURRENT_CONTAINER=$(docker ps -q --filter "name=${CONTAINER_NAME}")
    
    if [ -z "${CURRENT_CONTAINER}" ]; then
        echo -e "${YELLOW}没有运行中的容器。${NC}"
        return 0
    fi
    
    echo "停止容器：${CURRENT_CONTAINER}"
    docker stop "${CURRENT_CONTAINER}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}容器停止成功。${NC}"
        view_container_status
    else
        echo -e "${RED}容器停止失败。${NC}"
    fi
}

# 查看部署日志
view_deploy_logs() {
    echo -e "${BLUE}查看部署日志...${NC}"
    if ! check_docker; then
        return 1
    fi
    
    # 读取容器名称配置
    CONTAINER_NAME=$(read_config "container_name")
    if [ -z "${CONTAINER_NAME}" ]; then
        echo -e "${RED}错误：无法读取容器名称配置。${NC}"
        return 1
    fi
    
    CURRENT_CONTAINER=$(docker ps -q --filter "name=${CONTAINER_NAME}")
    
    if [ -z "${CURRENT_CONTAINER}" ]; then
        echo -e "${YELLOW}没有运行中的容器。${NC}"
        return 0
    fi
    
    echo "容器日志（最近50行）："
    echo "===================================================="
    docker logs --tail 50 "${CURRENT_CONTAINER}"
    echo "===================================================="
    
    echo ""
    echo -e "${BLUE}查看完整日志请使用：docker logs ${CURRENT_CONTAINER}${NC}"
}

# 主循环
main() {
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                deploy_latest
                ;;
            2)
                repull_and_deploy
                ;;
            3)
                view_current_version
                ;;
            4)
                view_container_status
                ;;
            5)
                restart_container
                ;;
            6)
                stop_container
                ;;
            7)
                view_deploy_logs
                ;;
            0)
                echo -e "${GREEN}感谢使用部署管理系统！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择，请重新输入。${NC}"
                ;;
        esac
        
        echo ""
        echo -n "按Enter键继续..."
        read
    done
}

# 检查是否直接运行脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi
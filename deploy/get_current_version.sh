#!/bin/bash

# 查看当前部署版本信息脚本

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 读取配置信息
read_config() {
    local key=$1
    python3 "${SCRIPT_DIR}/read_config.py" "$key" 2>/dev/null
}

# 获取配置值
CONTAINER_NAME=$(read_config "container_name")

# 验证配置是否成功读取
if [ -z "$CONTAINER_NAME" ]; then
    echo "错误：无法读取配置文件或配置信息不完整。"
    echo "请检查 ${SCRIPT_DIR}/docker_acr.json 文件是否存在且格式正确。"
    exit 1
fi

# 部署信息文件（放在app目录下，与deploy同级）
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"
APP_DIR="${PROJECT_ROOT}/app"
DEPLOY_INFO_FILE="${APP_DIR}/deploy.info"
VERSION_FILE="${APP_DIR}/version.txt"
DEPLOY_HISTORY_FILE="${APP_DIR}/deploy_history.log"

# 检查并创建APP_DIR目录
if [ ! -d "${APP_DIR}" ]; then
    echo "创建应用目录: ${APP_DIR}"
    mkdir -p "${APP_DIR}"
    if [ $? -ne 0 ]; then
        echo "错误：无法创建应用目录 ${APP_DIR}"
        exit 1
    fi
fi

# 检查Docker是否安装
docker --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "错误：未安装Docker或Docker服务未启动。"
    exit 1
fi

# 检查容器是否运行
echo "检查容器状态..."
CURRENT_CONTAINER=$(docker ps -q --filter "name=${CONTAINER_NAME}")

if [ -z "${CURRENT_CONTAINER}" ]; then
    echo "警告：容器 ${CONTAINER_NAME} 未运行。"
    
    # 检查是否有停止的容器
    STOPPED_CONTAINER=$(docker ps -aq --filter "name=${CONTAINER_NAME}")
    if [ -n "${STOPPED_CONTAINER}" ]; then
        echo "发现已停止的容器：${STOPPED_CONTAINER}"
        echo "使用最近停止的容器信息..."
        CURRENT_CONTAINER="${STOPPED_CONTAINER}"
    else
        echo "错误：未找到任何容器。"
        exit 1
    fi
fi

# 获取容器基本信息
echo ""
echo "===================================================="
echo "容器基本信息"
echo "===================================================="

CONTAINER_STATUS=$(docker inspect --format='{{.State.Status}}' "${CURRENT_CONTAINER}")
CONTAINER_IMAGE=$(docker inspect --format='{{.Config.Image}}' "${CURRENT_CONTAINER}")
CONTAINER_CREATED=$(docker inspect --format='{{.Created}}' "${CURRENT_CONTAINER}")
CONTAINER_STARTED=$(docker inspect --format='{{.State.StartedAt}}' "${CURRENT_CONTAINER}")

echo "容器ID: ${CURRENT_CONTAINER}"
echo "容器状态: ${CONTAINER_STATUS}"
echo "镜像: ${CONTAINER_IMAGE}"
echo "创建时间: ${CONTAINER_CREATED}"
if [ "${CONTAINER_STATUS}" = "running" ]; then
    echo "启动时间: ${CONTAINER_STARTED}"
fi

# 获取镜像详细信息
echo ""
echo "===================================================="
echo "镜像详细信息"
echo "===================================================="

IMAGE_ID=$(docker inspect --format='{{.Image}}' "${CURRENT_CONTAINER}")
IMAGE_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "${CONTAINER_IMAGE}" 2>/dev/null || echo "unknown")

# 获取镜像标签列表
echo "镜像ID: ${IMAGE_ID}"
echo "镜像Digest: ${IMAGE_DIGEST}"

# 获取相同镜像ID的所有标签
echo ""
echo "相同镜像ID的标签："
docker images --no-trunc --format 'table {{.Repository}}:{{.Tag}}\t{{.ID}}' | grep "${IMAGE_ID}" | grep -v "<none>" | sort

# 检查部署信息文件
if [ -f "${DEPLOY_INFO_FILE}" ]; then
    echo ""
    echo "===================================================="
    echo "部署信息文件内容"
    echo "===================================================="
    cat "${DEPLOY_INFO_FILE}"
fi

# 检查容器内的版本信息文件
echo ""
echo "===================================================="
echo "容器内版本信息"
echo "===================================================="

if docker exec "${CURRENT_CONTAINER}" test -f "${VERSION_FILE}" 2>/dev/null; then
    echo "容器内版本文件内容："
    docker exec "${CURRENT_CONTAINER}" cat "${VERSION_FILE}"
else
    echo "容器内未找到版本文件 ${VERSION_FILE}"
    
    # 尝试其他可能的版本文件位置
    ALTERNATIVE_PATHS=("/app/version.info" "/version.txt" "/app/version")
    for path in "${ALTERNATIVE_PATHS[@]}"; do
        if docker exec "${CURRENT_CONTAINER}" test -f "${path}" 2>/dev/null; then
            echo "在 ${path} 找到版本信息："
            docker exec "${CURRENT_CONTAINER}" cat "${path}"
            break
        fi
    done
fi

# 显示镜像历史（最近5条）
echo ""
echo "===================================================="
echo "镜像历史（最近5个）"
echo "===================================================="

IMAGE_REPO=$(echo "${CONTAINER_IMAGE}" | cut -d: -f1)
docker images --format 'table {{.Repository}}:{{.Tag}}\t{{.CreatedSince}}\t{{.Size}}' "${IMAGE_REPO}" | head -6

# 显示部署历史记录（最近10条）
echo ""
echo "===================================================="
echo "部署历史记录（最近10条）"
echo "===================================================="

if [ -f "${DEPLOY_HISTORY_FILE}" ]; then
    echo "部署历史文件: ${DEPLOY_HISTORY_FILE}"
    echo ""
    head -10 "${DEPLOY_HISTORY_FILE}"
else
    echo "未找到部署历史记录文件: ${DEPLOY_HISTORY_FILE}"
fi

echo ""
echo "===================================================="
echo "版本信息获取完成"
echo "===================================================="
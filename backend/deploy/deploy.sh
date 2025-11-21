#!/bin/bash

# 服务器端部署脚本
# 用于拉取最新镜像并部署应用

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 读取配置信息
read_config() {
    local key=$1
    python3 "${SCRIPT_DIR}/read_config.py" "$key" 2>/dev/null
}

# 获取配置值
ACR_REPO=$(read_config "acr_repo")
ACR_USER=$(read_config "acr_user")
ACR_REGISTRY=$(read_config "acr_registry")
ACR_PASSWORD=$(read_config "acr_password")
CONTAINER_NAME=$(read_config "container_name")
PORT=$(read_config "port")

# 验证配置是否成功读取
if [ -z "$ACR_REPO" ] || [ -z "$ACR_USER" ] || [ -z "$ACR_REGISTRY" ] || [ -z "$ACR_PASSWORD" ] || [ -z "$CONTAINER_NAME" ] || [ -z "$PORT" ]; then
    echo "错误：无法读取配置文件或配置信息不完整。"
    echo "请检查 ${SCRIPT_DIR}/docker_acr.conf 文件是否存在且格式正确。"
    exit 1
fi

# 部署信息文件（放在app目录下，与deploy同级）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

# 检查是否已登录ACR仓库
echo "检查ACR仓库登录状态..."
docker manifest inspect "${ACR_REPO}:latest" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "需要登录ACR仓库..."
    echo "当前使用的用户名：${ACR_USER}"
    echo "使用配置文件中的密码进行登录..."
    echo "${ACR_PASSWORD}" | docker login --username="${ACR_USER}" --password-stdin "${ACR_REGISTRY}"
    if [ $? -ne 0 ]; then
        echo "错误：ACR登录失败。"
        exit 1
    fi
    echo "ACR登录成功。"
fi

# 检查当前运行的容器
echo "检查当前运行的容器..."
CURRENT_CONTAINER=$(docker ps -q --filter "name=${CONTAINER_NAME}")
CURRENT_IMAGE=""

if [ -n "${CURRENT_CONTAINER}" ]; then
    echo "发现正在运行的容器：${CURRENT_CONTAINER}"
    CURRENT_IMAGE=$(docker inspect --format='{{.Config.Image}}' "${CURRENT_CONTAINER}")
    echo "当前运行的镜像：${CURRENT_IMAGE}"
fi

# 检查是否存在停止状态的容器（防止名称冲突）
STOPPED_CONTAINER=$(docker ps -aq --filter "name=${CONTAINER_NAME}")
if [ -n "${STOPPED_CONTAINER}" ] && [ "${STOPPED_CONTAINER}" != "${CURRENT_CONTAINER}" ]; then
    echo "发现停止状态的容器：${STOPPED_CONTAINER}"
    echo "删除停止状态的容器以防止名称冲突..."
    docker rm "${STOPPED_CONTAINER}"
    if [ $? -eq 0 ]; then
        echo "停止状态的容器已删除。"
    else
        echo "警告：无法删除停止状态的容器，可能会影响后续部署。"
    fi
fi

# 拉取最新镜像
echo "正在拉取最新镜像..."
docker pull "${ACR_REPO}:latest"
if [ $? -ne 0 ]; then
    echo "错误：镜像拉取失败。"
    exit 1
fi

# 获取拉取镜像的信息
LATEST_IMAGE="${ACR_REPO}:latest"
LATEST_IMAGE_ID=$(docker images --no-trunc --format '{{.ID}}' "${LATEST_IMAGE}")
LATEST_IMAGE_DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "${LATEST_IMAGE}" 2>/dev/null || echo "unknown")

# 检查是否需要更新
if [ "${CURRENT_IMAGE}" = "${LATEST_IMAGE}" ]; then
    echo "当前运行的镜像已是最新版本，无需更新。"
    
    # 检查镜像ID是否相同（确保确实是同一个镜像）
    CURRENT_IMAGE_ID=$(docker inspect --format='{{.Image}}' "${CURRENT_CONTAINER}" 2>/dev/null || echo "")
    if [ "${CURRENT_IMAGE_ID}" = "${LATEST_IMAGE_ID}" ]; then
        echo "镜像ID验证通过，当前部署已是最新版本。"
        exit 0
    else
        echo "警告：镜像标签相同但镜像ID不同，可能存在版本不一致。"
    fi
fi

# 停止并删除旧容器
if [ -n "${CURRENT_CONTAINER}" ]; then
    echo "停止并删除旧容器..."
    docker stop "${CURRENT_CONTAINER}"
    docker rm "${CURRENT_CONTAINER}"
fi

# 启动新容器
echo "启动新容器..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${PORT}:5000" \
    --restart unless-stopped \
    "${LATEST_IMAGE}"

if [ $? -ne 0 ]; then
    echo "错误：容器启动失败。"
    exit 1
fi

# 等待容器启动
echo "等待容器启动..."
sleep 10

# 检查容器状态
NEW_CONTAINER=$(docker ps -q --filter "name=${CONTAINER_NAME}")
if [ -z "${NEW_CONTAINER}" ]; then
    echo "错误：新容器启动失败。"
    exit 1
fi

# 获取容器内的版本信息
echo "获取部署版本信息..."
DEPLOY_TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# 获取镜像ID（短格式）和Digest（仅sha256部分）
SHORT_IMAGE_ID=$(echo "${LATEST_IMAGE_ID}" | cut -c 1-12)
IMAGE_DIGEST_ONLY=$(echo "${LATEST_IMAGE_DIGEST}" | sed 's/.*@sha256://')

# 尝试从容器内获取版本信息
if docker exec "${NEW_CONTAINER}" test -f "${VERSION_FILE}"; then
    docker exec "${NEW_CONTAINER}" cat "${VERSION_FILE}" > "${DEPLOY_INFO_FILE}"
    echo "部署时间: ${DEPLOY_TIMESTAMP}" >> "${DEPLOY_INFO_FILE}"
    echo "容器ID: ${NEW_CONTAINER}" >> "${DEPLOY_INFO_FILE}"
    echo "镜像: ${LATEST_IMAGE}" >> "${DEPLOY_INFO_FILE}"
    echo "镜像ID: ${SHORT_IMAGE_ID}" >> "${DEPLOY_INFO_FILE}"
    echo "镜像Digest: ${IMAGE_DIGEST_ONLY}" >> "${DEPLOY_INFO_FILE}"
else
    # 如果容器内没有版本文件，创建基本部署信息
    echo "Build Timestamp: ${DEPLOY_TIMESTAMP}" > "${DEPLOY_INFO_FILE}"
    echo "Build Tag: latest" >> "${DEPLOY_INFO_FILE}"
    echo "Image: ${LATEST_IMAGE}" >> "${DEPLOY_INFO_FILE}"
    echo "Image ID: ${SHORT_IMAGE_ID}" >> "${DEPLOY_INFO_FILE}"
    echo "Image Digest: ${IMAGE_DIGEST_ONLY}" >> "${DEPLOY_INFO_FILE}"
    echo "Container ID: ${NEW_CONTAINER}" >> "${DEPLOY_INFO_FILE}"
fi

# 记录部署历史（添加到文件最前端）
echo "记录部署历史..."
HISTORY_ENTRY="[${DEPLOY_TIMESTAMP}] DEPLOY - Container:${NEW_CONTAINER} Image:${LATEST_IMAGE} ImageID:${SHORT_IMAGE_ID} Digest:${IMAGE_DIGEST_ONLY}"
if [ -f "${DEPLOY_HISTORY_FILE}" ]; then
    # 如果文件存在，将新记录添加到最前面
    echo "${HISTORY_ENTRY}" > "${DEPLOY_HISTORY_FILE}.tmp"
    cat "${DEPLOY_HISTORY_FILE}" >> "${DEPLOY_HISTORY_FILE}.tmp"
    mv "${DEPLOY_HISTORY_FILE}.tmp" "${DEPLOY_HISTORY_FILE}"
else
    # 如果文件不存在，创建新文件
    echo "${HISTORY_ENTRY}" > "${DEPLOY_HISTORY_FILE}"
fi

# 显示部署信息
echo ""
echo "===================================================="
echo "部署完成！"
echo "===================================================="
echo "容器名称: ${CONTAINER_NAME}"
echo "容器ID: ${NEW_CONTAINER}"
echo "镜像: ${LATEST_IMAGE}"
echo "端口: ${PORT}"
echo "部署时间: ${DEPLOY_TIMESTAMP}"
echo ""
echo "版本信息已保存到: ${DEPLOY_INFO_FILE}"
echo "部署历史已记录到: ${DEPLOY_HISTORY_FILE}"

# 显示容器内的版本信息（如果存在）
if docker exec "${NEW_CONTAINER}" test -f "${VERSION_FILE}"; then
    echo "容器内版本信息："
    docker exec "${NEW_CONTAINER}" cat "${VERSION_FILE}"
fi

echo "===================================================="
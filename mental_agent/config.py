"""
Coze聊天机器人配置文件
只保留核心必要配置，删除冗余字段
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础配置
BASE_DIR = Path(__file__).parent

# Coze API核心配置（仅保留客户端用到的字段）
COZE_CONFIG = {
    'bot_id': os.getenv('COZE_BOT_ID', ''),    # 必填：Coze Bot ID
    'user_id': os.getenv('COZE_USER_ID', 'default_user'),  # 可选：自定义用户ID
    'api_token': os.getenv('COZE_API_TOKEN', ''),  # 必填：Coze API Token
    'base_url': os.getenv('COZE_BASE_URL', 'https://api.coze.cn/v3'),  # API基础地址
    'timeout': 60,  # 请求超时时间（秒）
}

# 服务器配置（与.env联动，支持环境变量覆盖）
SERVER_CONFIG = {
    'host': os.getenv('SERVER_HOST', '0.0.0.0'),  # 监听地址（默认所有网卡）
    'port': int(os.getenv('SERVER_PORT', 6001)),  # 端口（默认6001）
    'debug': os.getenv('DEBUG', 'false').lower() == 'true',  # 调试模式
    'allowed_origins': ['*'],  # CORS允许的源（生产环境建议指定具体域名）
    'max_request_size': 10 * 1024 * 1024,  # 最大请求大小（10MB）
}

# 创建日志目录（必要目录）
os.makedirs(BASE_DIR / 'logs', exist_ok=True)
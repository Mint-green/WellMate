"""
健康对话模块

提供健康相关的文本对话功能
"""

from flask import Blueprint

# 创建健康对话蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

# 导入路由
from . import routes
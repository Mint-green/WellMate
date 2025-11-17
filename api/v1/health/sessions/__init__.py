"""
会话管理模块

提供对话会话的创建、查询、管理功能
"""

from flask import Blueprint

# 创建会话管理蓝图
sessions_bp = Blueprint('sessions', __name__, url_prefix='/sessions')

# 导入路由
from . import routes
"""
身体健康会话模块

提供身体健康相关的对话功能
"""

from flask import Blueprint

# 创建身体健康对话蓝图
physical_bp = Blueprint('physical', __name__, url_prefix='/physical')

# 导入路由
from . import routes
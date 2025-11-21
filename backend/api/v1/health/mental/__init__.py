"""
心理健康会话模块

提供心理健康相关的对话功能
"""

from flask import Blueprint

# 创建心理健康对话蓝图
mental_bp = Blueprint('mental', __name__, url_prefix='/mental')

# 导入路由
from . import routes
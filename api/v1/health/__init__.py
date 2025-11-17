"""
健康管理模块

提供健康相关的功能接口
"""

from flask import Blueprint

# 创建健康管理蓝图
health_bp = Blueprint('health', __name__, url_prefix='/health')

# 导入子模块蓝图（在v1/__init__.py中注册）
from .chat import chat_bp
from .physical import physical_bp
from .mental import mental_bp
from .sessions import sessions_bp
from .data import data_bp
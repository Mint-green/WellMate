"""
认证管理模块

提供用户注册、登录等认证相关功能
"""

from flask import Blueprint

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 导入路由
from . import routes
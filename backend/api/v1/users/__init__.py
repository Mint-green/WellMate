"""
用户管理模块

提供用户信息管理、配置设置等功能
"""

from flask import Blueprint

# 创建用户管理蓝图
users_bp = Blueprint('users', __name__, url_prefix='/users')

# 导入路由
from . import routes
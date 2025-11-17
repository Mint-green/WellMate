"""
健康数据模块

提供健康数据同步和管理功能
"""

from flask import Blueprint

# 创建健康数据蓝图
data_bp = Blueprint('data', __name__, url_prefix='/data')

# 导入路由
from . import routes
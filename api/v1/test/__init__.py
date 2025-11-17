"""
测试模块

提供API测试和状态检查功能
"""

from flask import Blueprint

# 创建测试蓝图
test_bp = Blueprint('test', __name__, url_prefix='/test')

# 导入路由
from . import routes
# 用户管理API模块
from flask import Blueprint

# 创建用户管理蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

# 导入路由定义
from . import auth

# 导入模型定义
from . import models
"""
API v1 版本模块

提供健康助手后端API的v1版本实现
"""

from flask import Blueprint

# 创建v1版本的API蓝图
v1_bp = Blueprint('v1', __name__, url_prefix='/api/v1')

def register_v1_blueprints(app):
    """注册v1版本的所有蓝图"""
    from .auth import auth_bp
    from .users import users_bp
    from .health import health_bp
    from .test import test_bp
    
    # 注册健康模块的子蓝图
    from .health.chat import chat_bp
    from .health.sessions import sessions_bp
    from .health.data import data_bp
    from .health.physical import physical_bp
    from .health.mental import mental_bp
    
    health_bp.register_blueprint(chat_bp)
    health_bp.register_blueprint(sessions_bp)
    health_bp.register_blueprint(data_bp)
    health_bp.register_blueprint(physical_bp)
    health_bp.register_blueprint(mental_bp)
    
    # 注册子蓝图到v1蓝图
    v1_bp.register_blueprint(auth_bp)
    v1_bp.register_blueprint(users_bp)
    v1_bp.register_blueprint(health_bp)
    v1_bp.register_blueprint(test_bp)
    
    # 最后注册v1蓝图到应用
    app.register_blueprint(v1_bp)
    
    return [auth_bp, users_bp, health_bp, test_bp, chat_bp, sessions_bp, data_bp]
from .testapi import testapi_bp
from .health import health_bp, register_health_blueprints
from .user import user_bp

# 注册所有蓝图的函数
def register_blueprints(app):
    # 注册测试接口蓝图
    app.register_blueprint(testapi_bp)
    
    # 注册健康模块父蓝图
    app.register_blueprint(health_bp)
    
    # 注册用户管理蓝图
    app.register_blueprint(user_bp)
    
    # 注册健康模块的子蓝图，并应用响应装饰器
    blueprints = register_health_blueprints()
    for bp in blueprints:
        app.register_blueprint(bp)
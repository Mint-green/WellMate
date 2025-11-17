from .v1 import register_v1_blueprints

# 注册所有蓝图的函数
def register_blueprints(app):
    # 注册v1版本的所有API蓝图
    v1_blueprints = register_v1_blueprints(app)
    
    return v1_blueprints
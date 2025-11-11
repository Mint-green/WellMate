from flask import Blueprint, jsonify, request
from functools import wraps

# 创建健康相关的父蓝图
health_bp = Blueprint('health', __name__, url_prefix='/health')

# 为健康接口定义一个响应格式转换装饰器
def health_response_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 调用原始函数获取响应
        response = f(*args, **kwargs)
        
        # 如果响应是JSON格式的字典
        if isinstance(response, dict):
            # 添加health字段到响应中
            return jsonify({
                'health': {
                    'status': response.get('status'),
                    'message': response.get('message'),
                    'data': response.get('data')
                },
                'timestamp': request.timestamp if hasattr(request, 'timestamp') else None
            })
        
        # 如果响应是flask.Response对象，尝试修改其内容
        if hasattr(response, 'get_json'):
            try:
                data = response.get_json()
                if data and isinstance(data, dict):
                    # 创建新的响应，添加health字段
                    return jsonify({
                        'health': {
                            'status': data.get('status'),
                            'message': data.get('message'),
                            'data': data.get('data')
                        },
                        'timestamp': request.timestamp if hasattr(request, 'timestamp') else None
                    })
            except Exception:
                pass
        
        # 如果无法修改响应，返回原始响应
        return response
    return decorated_function

# 健康模块的中间件，在请求处理前后执行公共逻辑
@health_bp.before_app_request
def before_health_request():
    # 只处理/health路径下的请求
    if request.path.startswith('/health/'):
        # 可以在这里添加请求前的公共逻辑，如认证、日志记录等
        # 例如，添加时间戳到请求对象
        import time
        request.timestamp = int(time.time())

# 提供一个健康检查接口
@health_bp.route('/check', methods=['GET'])
@health_response_decorator
def health_check():
    return {
        'status': 'success',
        'message': 'Health service is running',
        'data': {
            'version': '1.0.0',
            'timestamp': request.timestamp if hasattr(request, 'timestamp') else None
        }
    }

# 导入子模块的蓝图
def register_health_blueprints():
    from .data import data_bp
    from .chat import chat_bp, physical_bp
    
    # 返回蓝图对象
    return data_bp, chat_bp, physical_bp
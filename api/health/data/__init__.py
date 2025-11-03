from flask import Blueprint
from .. import health_response_decorator

# 创建健康数据相关的蓝图
data_bp = Blueprint('healthdata', __name__, url_prefix='/health/data')

# 健康数据同步接口
@data_bp.route('/sync', methods=['POST'])
@health_response_decorator
def sync_health_data():
    # 这里可以添加数据同步的逻辑
    return {
        'status': 'success',
        'message': 'Health data synchronization started',
        'data': None
    }
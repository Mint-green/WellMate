"""
测试路由

提供API测试和状态检查接口
"""

from flask import jsonify
from . import test_bp

# 测试接口
@test_bp.route('', methods=['GET'])
def test_api():
    """测试API连通性"""
    return jsonify({
        'status': 'success',
        'message': 'API v1版本测试接口正常',
        'data': {
            'version': 'v1',
            'timestamp': '2024-01-01T10:00:00Z'
        }
    })

# 健康检查接口
@test_bp.route('/health', methods=['GET'])
def health_check():
    """API健康检查"""
    return jsonify({
        'status': 'success',
        'message': 'API v1版本健康状态正常',
        'data': {
            'health': 'ok',
            'timestamp': '2024-01-01T10:00:00Z'
        }
    })
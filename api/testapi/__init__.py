from flask import Blueprint, jsonify

# 创建测试接口的蓝图
testapi_bp = Blueprint('testapi', __name__, url_prefix='/testapi')

# 测试接口路由
@testapi_bp.route('/test', methods=['GET'])
def test_api():
    return jsonify({
        'status': 'success',
        'message': 'This is a test API endpoint',
        'data': None
    })
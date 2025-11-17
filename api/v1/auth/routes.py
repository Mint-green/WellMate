"""
认证管理路由

提供用户注册、登录等认证相关接口
"""

from flask import request, jsonify
from . import auth_bp
import logging

logger = logging.getLogger(__name__)

# 导入数据库管理器
try:
    from ..users.user_db_manager import user_db_manager
except ImportError:
    logger.error("无法导入user_db_manager，请确保数据库模块可用")
    user_db_manager = None

# 导入JWT工具
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from utils.jwt_utils import generate_access_token, generate_refresh_token
    JWT_AVAILABLE = True
except ImportError as e:
    logger.error(f"无法导入JWT工具，请确保jwt_utils模块可用: {e}")
    JWT_AVAILABLE = False

# 用户注册接口
@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 检查必需字段
    required_fields = ['username', 'password', 'full_name']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error',
                'message': f'缺少必需字段: {field}',
                'error_code': 'INVALID_REQUEST'
            }), 400
    
    username = data['username']
    
    try:
        # 使用数据库创建用户
        user = user_db_manager.create_user(
            username=username,
            password=data['password'],
            full_name=data['full_name'],
            gender=data.get('gender'),
            birth_date=data.get('birth_date'),
            age=data.get('age'),
            settings=data.get('settings')
        )
        
        logger.info(f"用户注册成功: {username} (UUID: {user['uuid']})")
        
        return jsonify({
            'status': 'success',
            'message': '用户注册成功',
            'data': {
                'uuid': user['uuid'],
                'username': username
            }
        })
        
    except ValueError as e:
        # 用户名已存在
        return jsonify({
            'status': 'error',
            'message': str(e),
            'error_code': 'USER_ALREADY_EXISTS'
        }), 409
        
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '用户注册失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500


# token刷新接口
@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """刷新access token"""
    data = request.get_json()
    
    # 检查必需字段
    if 'refresh_token' not in data:
        return jsonify({
            'status': 'error',
            'message': '缺少refresh_token',
            'error_code': 'INVALID_REQUEST'
        }), 400
    
    refresh_token = data['refresh_token']
    
    try:
        # 导入刷新函数
        from utils.jwt_utils import refresh_token as jwt_refresh_token
        
        # 刷新token
        result = jwt_refresh_token(refresh_token)
        
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'refresh_token无效或已过期',
                'error_code': 'INVALID_REFRESH_TOKEN'
            }), 401
        
        logger.info(f"token刷新成功: {result['username']} (UUID: {result['uuid']})")
        
        return jsonify({
            'status': 'success',
            'message': 'token刷新成功',
            'data': {
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'token_type': 'Bearer',
                'expires_in': 24 * 60 * 60,  # 24小时
                'uuid': result['uuid'],
                'username': result['username']
            }
        })
        
    except Exception as e:
        logger.error(f"token刷新失败: {e}")
        return jsonify({
            'status': 'error',
            'message': 'token刷新失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 用户登录接口
@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    # 检查必需字段
    if 'username' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'message': '缺少用户名或密码',
            'error_code': 'INVALID_REQUEST'
        }), 400
    
    username = data['username']
    password = data['password']
    
    try:
        # 使用数据库进行用户认证
        user = user_db_manager.authenticate_user(username, password)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户名或密码错误',
                'error_code': 'AUTHENTICATION_FAILED'
            }), 401
        
        # 检查账户是否激活
        if not user['is_active']:
            return jsonify({
                'status': 'error',
                'message': '账户未激活',
                'error_code': 'ACCOUNT_INACTIVE'
            }), 403
        
        # 生成JWT token
        if generate_access_token and generate_refresh_token:
            access_token = generate_access_token(user['uuid'], username)
            refresh_token = generate_refresh_token(user['uuid'], username)
        else:
            logger.warning("JWT工具不可用，无法生成token")
            access_token = None
            refresh_token = None
        
        logger.info(f"用户登录成功: {username} (UUID: {user['uuid']})")
        
        response_data = {
            'uuid': user['uuid'],
            'username': username,
            'full_name': user['full_name']
        }
        
        # 如果token生成成功，添加到响应中
        if access_token and refresh_token:
            response_data.update({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 24 * 60 * 60  # 24小时
            })
        
        return jsonify({
            'status': 'success',
            'message': '登录成功',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '登录失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500
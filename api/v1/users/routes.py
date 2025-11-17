"""
用户管理路由

提供用户信息管理、配置设置等接口
"""

from flask import request, jsonify
from . import users_bp
import logging

logger = logging.getLogger(__name__)

# 导入JWT验证装饰器和数据库管理器
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from utils.jwt_utils import token_required
    JWT_AVAILABLE = True
except ImportError as e:
    logger.error(f"无法导入JWT工具，请确保jwt_utils模块可用: {e}")
    JWT_AVAILABLE = False
    token_required = None

try:
    from .user_db_manager import user_db_manager
except ImportError:
    logger.error("无法导入user_db_manager，请确保数据库模块可用")
    user_db_manager = None

# 获取用户信息接口
@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """获取用户信息"""
    try:
        # 从请求上下文中获取用户信息
        user_uuid = request.uuid
        username = request.username
        
        # 从数据库获取用户详细信息
        user = user_db_manager.get_user_by_uuid(user_uuid)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在',
                'error_code': 'USER_NOT_FOUND'
            }), 404
        
        logger.info(f"获取用户信息成功: {username} (UUID: {user_uuid})")
        
        # 返回用户信息（排除敏感信息）
        return jsonify({
            'status': 'success',
            'message': '获取用户信息成功',
            'data': {
                'uuid': user['uuid'],
                'username': user['username'],
                'full_name': user['full_name'],
                'gender': user.get('gender'),
                'birth_date': user.get('birth_date'),
                'age': user.get('age'),
                'is_active': user['is_active'],
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '获取用户信息失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 更新用户配置接口
@users_bp.route('/settings', methods=['PUT'])
@token_required
def update_settings():
    """更新用户配置"""
    data = request.get_json()
    
    # 检查必需字段
    if not data:
        return jsonify({
            'status': 'error',
            'message': '缺少配置数据',
            'error_code': 'INVALID_REQUEST'
        }), 400
    
    try:
        # 从请求上下文中获取用户信息
        user_uuid = request.uuid
        username = request.username
        
        # 更新用户配置
        success = user_db_manager.update_user_settings_by_uuid(user_uuid, data)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': '更新用户配置失败',
                'error_code': 'UPDATE_FAILED'
            }), 500
        
        logger.info(f"更新用户配置成功: {username} (UUID: {user_uuid})")
        
        return jsonify({
            'status': 'success',
            'message': '更新用户配置成功',
            'data': {
                'uuid': user_uuid,
                'username': username,
                'updated_settings': data
            }
        })
        
    except Exception as e:
        logger.error(f"更新用户配置失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '更新用户配置失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500
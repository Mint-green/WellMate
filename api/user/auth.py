# 用户认证模块
from flask import request, jsonify
from . import user_bp
from ..health import health_response_decorator
from .user_db_manager import user_db_manager
import uuid
import datetime
import os
import logging

logger = logging.getLogger(__name__)

@user_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册接口"""
    data = request.get_json()
    
    # 检查必需字段
    required_fields = ['username', 'password', 'full_name']
    for field in required_fields:
        if field not in data or not data[field]:
            return {
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': f'缺少必需字段: {field}'
                }
            }, 400
    
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
        
        logger.info(f"用户注册成功: {username} (ID: {user['id']})")
        
        return {
            'status': 'success',
            'message': '用户注册成功',
            'user_id': user['id'],
            'uuid': user['uuid']
        }
        
    except ValueError as e:
        # 用户名已存在
        return {
            'error': {
                'code': 'USER_ALREADY_EXISTS',
                'message': str(e)
            }
        }, 409
        
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return {
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '用户注册失败，请稍后重试'
            }
        }, 500

@user_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    data = request.get_json()
    
    # 检查必需字段
    if 'username' not in data or 'password' not in data:
        return {
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '缺少用户名或密码'
            }
        }, 400
    
    username = data['username']
    password = data['password']
    
    try:
        # 使用数据库进行用户认证
        user = user_db_manager.authenticate_user(username, password)
        
        if not user:
            return {
                'error': {
                    'code': 'AUTHENTICATION_FAILED',
                    'message': '用户名或密码错误'
                }
            }, 401
        
        # 检查账户是否激活
        if not user['is_active']:
            return {
                'error': {
                    'code': 'ACCOUNT_INACTIVE',
                    'message': '账户未激活'
                }
            }, 403
        
        logger.info(f"用户登录成功: {username} (ID: {user['id']})")
        
        return {
            'status': 'success',
            'user_id': user['id'],
            'uuid': user['uuid'],
            'username': username,
            'full_name': user['full_name']
        }
        
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return {
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '登录失败，请稍后重试'
            }
        }, 500

@user_bp.route('/auth/profile', methods=['GET'])
@health_response_decorator
def get_profile():
    """获取用户信息接口"""
    # 从查询参数获取用户UUID
    user_uuid = request.args.get('uuid')
    username = request.args.get('username')
    
    # 必须提供uuid或username
    if not user_uuid and not username:
        return {
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '必须提供uuid或username参数'
            }
        }, 400
    
    try:
        # 根据UUID或用户名查找用户
        user = None
        if user_uuid:
            user = user_db_manager.get_user_by_uuid(user_uuid)
        elif username:
            user = user_db_manager.get_user_by_username(username)
        
        if not user:
            return {
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, 404
        
        # 移除密码字段
        user_info = {key: value for key, value in user.items() if key != 'password'}
        
        logger.info(f"获取用户信息成功: {user['username']} (ID: {user['id']})")
        
        return {
            'status': 'success',
            'user': user_info
        }
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return {
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '获取用户信息失败，请稍后重试'
            }
        }, 500


@user_bp.route('/auth/settings', methods=['PUT'])
@health_response_decorator
def update_settings():
    """更新用户设置接口"""
    data = request.get_json()
    
    # 验证请求数据
    if not data or 'uuid' not in data:
        return {
            'error': {
                'code': 'INVALID_REQUEST',
                'message': '必须提供uuid参数'
            }
        }, 400
    
    user_uuid = data['uuid']
    
    try:
        # 查找用户
        user = user_db_manager.get_user_by_uuid(user_uuid)
        
        if not user:
            return {
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': '用户不存在'
                }
            }, 404
        
        # 更新设置
        if 'settings' in data:
            success = user_db_manager.update_user_settings(user_uuid, data['settings'])
            if not success:
                return {
                    'error': {
                        'code': 'UPDATE_FAILED',
                        'message': '设置更新失败'
                    }
                }, 500
        
        # 更新个人资料
        if 'profile' in data:
            success = user_db_manager.update_user_profile(user_uuid, data['profile'])
            if not success:
                return {
                    'error': {
                        'code': 'UPDATE_FAILED',
                        'message': '个人资料更新失败'
                    }
                }, 500
        
        logger.info(f"用户设置更新成功: {user['username']} (ID: {user['id']})")
        
        return {
            'status': 'success',
            'message': '设置更新成功'
        }
        
    except Exception as e:
        logger.error(f"更新用户设置失败: {e}")
        return {
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '更新设置失败，请稍后重试'
            }
        }, 500
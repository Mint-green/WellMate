"""
JWT工具模块

提供JWT token的生成、验证和刷新功能
"""

import jwt
import datetime
from flask import request, jsonify
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = "health_assistant_secret_key_2024"  # 生产环境应该使用环境变量
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # token有效期24小时
JWT_REFRESH_EXPIRATION_DAYS = 7  # refresh token有效期7天


def generate_access_token(uuid, username):
    """
    生成访问token
    
    Args:
        uuid: 用户UUID
        username: 用户名
        
    Returns:
        str: JWT token
    """
    payload = {
        'uuid': uuid,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow(),
        'type': 'access'
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def generate_refresh_token(uuid, username):
    """
    生成刷新token
    
    Args:
        uuid: 用户UUID
        username: 用户名
        
    Returns:
        str: 刷新token
    """
    payload = {
        'uuid': uuid,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_REFRESH_EXPIRATION_DAYS),
        'iat': datetime.datetime.utcnow(),
        'type': 'refresh'
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    """
    验证token有效性
    
    Args:
        token: JWT token
        
    Returns:
        dict: token payload或None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token已过期")
        return None
    except jwt.InvalidTokenError:
        logger.warning("无效的token")
        return None


def token_required(f):
    """
    JWT token验证装饰器
    
    Args:
        f: 被装饰的函数
        
    Returns:
        function: 装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'status': 'error',
                'message': '缺少认证token',
                'error_code': 'MISSING_TOKEN'
            }), 401
        
        # 检查Bearer格式
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'status': 'error',
                'message': 'token格式错误，应为Bearer格式',
                'error_code': 'INVALID_TOKEN_FORMAT'
            }), 401
        
        token = auth_header.split(' ')[1]
        
        # 验证token
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'status': 'error',
                'message': 'token无效或已过期',
                'error_code': 'INVALID_TOKEN'
            }), 401
        
        # 检查token类型
        if payload.get('type') != 'access':
            return jsonify({
                'status': 'error',
                'message': 'token类型错误，需要access token',
                'error_code': 'INVALID_TOKEN_TYPE'
            }), 401
        
        # 创建用户信息字典
        current_user = {
            'uuid': payload['uuid'],
            'username': payload['username']
        }
        
        # 将用户信息添加到请求上下文
        request.uuid = payload['uuid']
        request.username = payload['username']
        
        # 将用户信息作为参数传递给被装饰函数
        return f(current_user, *args, **kwargs)
    
    return decorated_function


def refresh_token(refresh_token):
    """
    刷新access token
    
    Args:
        refresh_token: 刷新token
        
    Returns:
        dict: 新的access token和refresh token
    """
    # 验证refresh token
    payload = verify_token(refresh_token)
    if not payload or payload.get('type') != 'refresh':
        return None
    
    # 生成新的access token
    new_access_token = generate_access_token(payload['uuid'], payload['username'])
    
    # 生成新的refresh token（可选，可以延长有效期）
    new_refresh_token = generate_refresh_token(payload['uuid'], payload['username'])
    
    return {
        'access_token': new_access_token,
        'refresh_token': new_refresh_token,
        'uuid': payload['uuid'],
        'username': payload['username']
    }


def get_token_expiration(token):
    """
    获取token过期时间
    
    Args:
        token: JWT token
        
    Returns:
        datetime: 过期时间或None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={'verify_exp': False})
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            return datetime.datetime.fromtimestamp(exp_timestamp)
        return None
    except jwt.InvalidTokenError:
        return None
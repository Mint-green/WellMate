"""
健康数据路由

提供健康数据查询接口，基于数据库的真实业务逻辑
"""

from flask import request, jsonify
import logging
from . import data_bp

logger = logging.getLogger(__name__)

# 导入数据库管理器和JWT验证装饰器
try:
    from .health_data_manager import health_data_manager
except ImportError:
    logger.error("无法导入health_data_manager，请确保健康数据模块可用")
    health_data_manager = None
# 尝试导入JWT验证装饰器
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from utils.jwt_utils import token_required
    JWT_AVAILABLE = True
except ImportError as e:
    logger.error(f"无法导入JWT工具，请确保jwt_utils模块可用: {e}")
    JWT_AVAILABLE = False

# 获取健康数据接口
@data_bp.route('', methods=['GET'])
@token_required
def get_health_data(current_user):
    """获取健康数据 - 基于数据库的真实业务逻辑"""
    
    # 从token中获取用户UUID
    user_uuid = request.uuid
    data_type = request.args.get('type', 'all')
    
    # 验证数据类型
    valid_types = ['all', 'heart_rate', 'steps', 'sleep', 'weight', 'blood_pressure', 'calories']
    if data_type not in valid_types:
        return jsonify({
            'status': 'error',
            'message': f'不支持的数据类型: {data_type}，支持的类型: {valid_types}',
            'error_code': 'INVALID_DATA_TYPE'
        }), 400
    
    try:
        # 使用数据库查询健康数据
        health_data = health_data_manager.get_health_data(user_uuid, data_type)
        
        if not health_data:
            return jsonify({
                'status': 'success',
                'message': '未找到相关健康数据',
                'data': {
                    'uuid': user_uuid,
                    'data_type': data_type,
                    'health_data': {}
                }
            })
        
        logger.info(f"获取健康数据成功: 用户 {user_uuid}, 类型 {data_type}")
        
        return jsonify({
            'status': 'success',
            'message': '获取健康数据成功',
            'data': {
                'uuid': user_uuid,
                'data_type': data_type,
                'health_data': health_data
            }
        })
        
    except Exception as e:
        logger.error(f"获取健康数据失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '获取健康数据失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 添加健康数据接口
@data_bp.route('', methods=['POST'])
@token_required
def add_health_data(current_user):
    """添加健康数据 - 基于数据库的真实业务逻辑"""
    
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['data_type', 'value']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error',
                'message': f'缺少必需字段: {field}',
                'error_code': 'MISSING_FIELD'
            }), 400
    
    # 从token中获取用户UUID
    user_uuid = request.uuid
    data_type = data['data_type']
    
    # 验证数据类型
    valid_types = ['heart_rate', 'steps', 'sleep', 'weight', 'blood_pressure', 'calories']
    if data_type not in valid_types:
        return jsonify({
            'status': 'error',
            'message': f'不支持的数据类型: {data_type}，支持的类型: {valid_types}',
            'error_code': 'INVALID_DATA_TYPE'
        }), 400
    
    try:
        # 使用数据库添加健康数据
        success = health_data_manager.add_health_data(
            user_uuid=user_uuid,
            data_type=data_type,
            value=data['value'],
            timestamp=data.get('timestamp'),
            metadata=data.get('metadata', {})
        )
        
        if success:
            logger.info(f"添加健康数据成功: 用户 {user_uuid}, 类型 {data_type}")
            return jsonify({
                'status': 'success',
                'message': '健康数据添加成功',
                'data': {
                    'uuid': user_uuid,
                    'data_type': data_type,
                    'value': data['value']
                }
            })
        else:
            logger.error(f"添加健康数据失败: 用户 {user_uuid}, 类型 {data_type}")
            return jsonify({
                'status': 'error',
                'message': '健康数据添加失败',
                'error_code': 'ADD_FAILED'
            }), 500
            
    except Exception as e:
        logger.error(f"添加健康数据失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '健康数据添加失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500

# 获取健康数据统计接口
@data_bp.route('/stats', methods=['GET'])
@token_required
def get_health_stats(current_user):
    """获取健康数据统计 - 基于数据库的真实业务逻辑"""
    
    # 从token中获取用户UUID
    user_uuid = request.uuid
    period = request.args.get('period', 'week')  # day, week, month
    
    # 验证统计周期
    valid_periods = ['day', 'week', 'month']
    if period not in valid_periods:
        return jsonify({
            'status': 'error',
            'message': f'不支持的统计周期: {period}，支持的周期: {valid_periods}',
            'error_code': 'INVALID_PERIOD'
        }), 400
    
    try:
        # 使用数据库获取健康数据统计
        stats = health_data_manager.get_health_stats(user_uuid, period)
        
        logger.info(f"获取健康数据统计成功: 用户 {user_uuid}, 周期 {period}")
        
        return jsonify({
            'status': 'success',
            'message': '获取健康数据统计成功',
            'data': {
                'uuid': user_uuid,
                'period': period,
                'stats': stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取健康数据统计失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '获取健康数据统计失败，请稍后重试',
            'error_code': 'INTERNAL_ERROR'
        }), 500
"""
身体健康对话路由

提供身体健康相关的文本对话接口，基于Coze AI模型提供专业的健康建议
"""

from flask import request, jsonify, Response, stream_with_context
import requests
import json
import uuid
import os
import logging
import datetime
from . import physical_bp
from utils.jwt_utils import token_required
from ..sessions.session_manager import session_manager

logger = logging.getLogger(__name__)

# === Coze API 配置 ===
API_KEY = os.getenv("COZE_API_KEY", "pat_DyjwNAuK4thhVGMDE7WusSNFPFYwfiEEwYOs7WbOoZ9QJjNpXoQXPkNERk2Ld2aO")
BOT_ID = "7559087768224432170"  # Coze Agent ID
BASE_URL = "https://api.coze.cn/open_api/v2/chat"

# === 请求头 ===
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# === 生成唯一会话ID ===
def generate_conversation_id():
    return str(uuid.uuid4())

# === 处理会话和消息存储 ===
def handle_session_and_storage(user_uuid, session_id, user_input, ai_response):
    """
    处理会话创建和消息存储
    
    Args:
        user_uuid: 用户UUID
        session_id: 会话ID（可为None）
        user_input: 用户输入
        ai_response: AI回复
        
    Returns:
        tuple: (实际使用的session_id, conversation_id, 是否创建了新会话)
    """
    actual_session_id = session_id
    is_new_session = False
    
    try:
        # 如果没有提供session_id，创建新会话
        if not actual_session_id:
            session_info = session_manager.create_session(user_uuid, 'physical')
            if session_info:
                actual_session_id = session_info['session_id']
                is_new_session = True
                logger.info(f"创建新会话: {actual_session_id}")
            else:
                logger.error("创建新会话失败")
                return None, None, False
        else:
            # 检查会话是否存在且属于当前用户
            session_info = session_manager.get_session(actual_session_id)
            if not session_info or session_info['user_uuid'] != user_uuid:
                logger.warning(f"会话不存在或不属于当前用户: {actual_session_id}")
                # 创建新会话
                session_info = session_manager.create_session(user_uuid, 'physical')
                if session_info:
                    actual_session_id = session_info['session_id']
                    is_new_session = True
                    logger.info(f"创建新会话替代无效会话: {actual_session_id}")
                else:
                    logger.error("创建新会话失败")
                    return None, None, False
        
        # 获取或创建conversation_id
        conversation_id = session_manager.get_or_create_conversation_id(actual_session_id)
        
        # 存储用户消息
        if user_input:
            session_manager.add_message(actual_session_id, 'user', user_input, {
                'conversation_id': conversation_id,
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        # 存储AI回复
        if ai_response:
            session_manager.add_message(actual_session_id, 'assistant', ai_response, {
                'conversation_id': conversation_id,
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        return actual_session_id, conversation_id, is_new_session
        
    except Exception as e:
        logger.error(f"处理会话存储异常: {e}")
        return actual_session_id, None, is_new_session

# === 调用AI模型处理健康对话 ===
def call_health_agent(user_input, session_id=None, user_uuid=None):
    """调用Coze AI模型处理身体健康对话"""
    
    try:
        # 处理会话存储（仅在提供了user_uuid时）
        conversation_id = None
        actual_session_id = session_id
        is_new_session = False
        
        if user_uuid and user_uuid != "anonymous_user":
            actual_session_id, conversation_id, is_new_session = handle_session_and_storage(
                user_uuid, session_id, user_input, None  # 先不存储AI回复
            )
            
            if not actual_session_id:
                logger.error("会话存储失败")
                return {
                    "status": "error",
                    "message": "会话管理失败，请重试",
                    "data": None
                }
        
        # 如果没有conversation_id（匿名用户或新会话），生成一个
        if not conversation_id:
            conversation_id = generate_conversation_id()
        
        # 构造请求体
        payload = {
            "conversation_id": conversation_id,
            "bot_id": BOT_ID,
            "user": user_uuid or "anonymous_user",
            "query": user_input,
            "stream": False
        }
        
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            logger.error(f"AI模型调用失败: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"AI服务暂时不可用，请稍后重试",
                "data": None
            }

        res = response.json()
        messages = res.get("messages", [])

        # 从返回中提取 answer 类型的消息
        ai_response = None
        for msg in messages:
            if msg.get("type") == "answer":
                content = msg.get("content", "").strip()
                if content:
                    ai_response = content
                    logger.info(f"身体健康对话处理成功: {user_input[:50]}...")
                    break

        # 如果没有找到有效回复
        if not ai_response:
            logger.warning("AI模型未返回有效回复")
            return {
                "status": "warning",
                "message": "AI模型暂时无法处理您的请求，请稍后重试",
                "data": None
            }
        
        # 存储AI回复（仅在提供了user_uuid时）
        if user_uuid and user_uuid != "anonymous_user":
            session_manager.add_message(actual_session_id, 'assistant', ai_response, {
                'conversation_id': conversation_id,
                'timestamp': datetime.datetime.now().isoformat()
            })

        # 构建响应数据
        response_data = {
            "response": ai_response,
            "user_input": user_input,
            "type": "physical",
            "conversation_id": conversation_id
        }
        
        # 添加会话相关信息（如果适用）
        if actual_session_id:
            response_data["session_id"] = actual_session_id
            response_data["is_new_session"] = is_new_session

        return {
            "status": "success",
            "message": "身体健康对话处理完成",
            "data": response_data
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return {
            "status": "error",
            "message": "网络连接失败，请检查网络后重试",
            "data": None
        }
    except json.JSONDecodeError:
        logger.error(f"JSON解析失败: {response.text[:200]}")
        return {
            "status": "error",
            "message": "服务响应格式错误，请稍后重试",
            "data": None
        }
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return {
            "status": "error",
            "message": "系统内部错误，请稍后重试",
            "data": None
        }

# === 非流式对话接口 ===
@physical_bp.route('/text', methods=['POST'])
@token_required
def physical_text_chat(current_user):
    """身体健康对话接口（非流式）"""
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体必须为JSON格式"
        }), 400
    
    message = data.get('message')
    if not message:
        return jsonify({
            "status": "error",
            "message": "message字段不能为空"
        }), 400
    
    # 从token中获取user_uuid
    user_uuid = current_user.get('uuid')
    if not user_uuid:
        return jsonify({
            "status": "error",
            "message": "用户身份验证失败"
        }), 401
    
    # 获取可选的session_id
    session_id = data.get('session_id')
    
    # 调用AI模型
    result = call_health_agent(message, session_id, user_uuid)
    
    # 根据结果状态返回响应
    if result['status'] == 'success':
        return jsonify(result), 200
    elif result['status'] == 'warning':
        return jsonify(result), 200
    else:
        return jsonify(result), 500

# === 流式对话接口 ===
@physical_bp.route('/text/stream', methods=['POST'])
@token_required
def physical_text_chat_stream(current_user):
    """身体健康对话接口（流式）"""
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            "status": "error",
            "message": "请求体必须为JSON格式"
        }), 400
    
    message = data.get('message')
    if not message:
        return jsonify({
            "status": "error",
            "message": "message字段不能为空"
        }), 400
    
    # 从token中获取user_uuid
    user_uuid = current_user.get('uuid')
    if not user_uuid:
        return jsonify({
            "status": "error",
            "message": "用户身份验证失败"
        }), 401
    
    # 获取可选的session_id
    session_id = data.get('session_id')
    
    # 构造流式响应
    def generate():
        # 模拟流式响应（实际应调用流式AI接口）
        result = call_health_agent(message, session_id, user_uuid)
        
        if result['status'] == 'success':
            response_data = result['data']
            # 模拟分块输出
            response_text = response_data.get('response', '')
            chunk_size = 50
            
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i+chunk_size]
                yield f"data: {json.dumps({'chunk': chunk, 'type': 'chunk'})}\n\n"
                
            # 发送完成信号
            yield f"data: {json.dumps({'type': 'complete', 'data': response_data})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': result['message']})}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/plain')
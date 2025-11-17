"""
心理健康对话路由

提供心理健康相关的文本对话接口，基于Coze AI模型提供专业的心理支持和建议
"""

from flask import request, jsonify, Response, stream_with_context
import requests
import json
import uuid
import os
import logging
from . import mental_bp
from ..sessions.session_manager import SessionManager

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

# === 会话和存储处理 ===
def handle_session_and_storage(user_uuid, session_id, message, response_text, conversation_id=None):
    """处理会话管理和消息存储"""
    session_manager = SessionManager()
    
    # 如果提供了session_id，验证会话是否存在
    if session_id:
        existing_session = session_manager.get_session(session_id)
        if not existing_session:
            # 会话不存在，创建新会话（使用general类型，因为数据库ENUM不支持mental）
            new_session = session_manager.create_session(user_uuid, "general")
            if new_session:
                session_id = new_session.get('session_id')
            else:
                logger.error("创建新会话失败")
                return {
                    "session_id": None,
                    "conversation_id": conversation_id or str(uuid.uuid4())
                }
    else:
        # 创建新会话（使用general类型，因为数据库ENUM不支持mental）
        new_session = session_manager.create_session(user_uuid, "general")
        if new_session:
            session_id = new_session.get('session_id')
        else:
            logger.error("创建新会话失败")
            return {
                "session_id": None,
                "conversation_id": conversation_id or str(uuid.uuid4())
            }
    
    # 如果session_id仍然为None，则无法存储消息，但返回conversation_id
    if not session_id:
        return {
            "session_id": None,
            "conversation_id": conversation_id or str(uuid.uuid4())
        }
    
    # 获取或创建conversation_id
    if not conversation_id:
        conversation_id = session_manager.get_or_create_conversation_id(session_id)
    
    # 存储用户消息
    user_metadata = {"conversation_id": conversation_id}
    session_manager.add_message(session_id, "user", message, user_metadata)
    
    # 存储AI回复
    assistant_metadata = {"conversation_id": conversation_id}
    session_manager.add_message(session_id, "assistant", response_text, assistant_metadata)
    
    return {
        "session_id": session_id,
        "conversation_id": conversation_id
    }

# === 调用AI模型处理心理健康对话 ===
def call_mental_health_agent(user_input, session_id=None, user_uuid=None, conversation_id=None):
    """调用Coze AI模型处理心理健康对话"""
    
    # 如果提供了conversation_id，则使用现有会话，否则创建新会话
    if not conversation_id:
        conversation_id = generate_conversation_id()
    
    # 构造请求体，特别针对心理健康问题
    payload = {
        "conversation_id": conversation_id,
        "bot_id": BOT_ID,
        "user": user_uuid or "anonymous_user",
        "query": user_input,
        "stream": False
    }
    
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            logger.error(f"AI模型调用失败: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "message": f"心理支持服务暂时不可用，请稍后重试",
                "data": None
            }

        res = response.json()
        messages = res.get("messages", [])

        # 从返回中提取 answer 类型的消息
        for msg in messages:
            if msg.get("type") == "answer":
                content = msg.get("content", "").strip()
                if content:
                    logger.info(f"心理健康对话处理成功: {user_input[:50]}...")
                    return {
                        "status": "success",
                        "message": "心理健康对话处理完成",
                        "data": {
                            "response": content,
                            "user_input": user_input,
                            "type": "mental",
                            "conversation_id": conversation_id
                        }
                    }

        # 如果没有找到有效回复
        logger.warning("AI模型未返回有效回复")
        return {
            "status": "warning",
            "message": "心理支持服务暂时无法处理您的请求，请稍后重试",
            "data": None
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

# === 心理健康文本对话接口（非流式版本） ===
@mental_bp.route('/text', methods=['POST'])
def mental_text_chat():
    """心理健康文本对话 - 基于AI模型的真实业务逻辑"""
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            'status': 'error',
            'message': '请求数据格式错误',
            'error_code': 'INVALID_REQUEST'
        }), 400
    
    user_input = data.get('message')
    if not user_input:
        return jsonify({
            'status': 'error',
            'message': '缺少message字段',
            'error_code': 'MISSING_FIELD'
        }), 400
    
    # 获取会话相关参数
    session_id = data.get('session_id')
    user_uuid = data.get('user_uuid')
    
    # 获取或创建conversation_id
    conversation_id = None
    if session_id:
        session_manager = SessionManager()
        conversation_id = session_manager.get_or_create_conversation_id(session_id)
    
    # 调用AI模型处理对话
    result = call_mental_health_agent(user_input, session_id, user_uuid, conversation_id)
    
    # 处理会话和存储
    if result['status'] == 'success':
        session_info = handle_session_and_storage(
            user_uuid, 
            session_id, 
            user_input, 
            result['data']['response'],
            conversation_id
        )
        
        # 更新返回结果，包含会话信息
        result['data']['session_id'] = session_info['session_id']
        result['data']['conversation_id'] = session_info['conversation_id']
    
    # 返回处理结果
    if result['status'] == 'success':
        return jsonify(result)
    else:
        return jsonify(result), 500

# === 心理健康文本对话接口（流式版本） ===
@mental_bp.route('/text/stream', methods=['POST'])
def mental_text_chat_stream():
    """心理健康文本对话（流式） - 基于AI模型的真实业务逻辑"""
    
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({
            'status': 'error',
            'message': '请求数据格式错误',
            'error_code': 'INVALID_REQUEST'
        }), 400
    
    user_input = data.get('message')
    if not user_input:
        return jsonify({
            'status': 'error',
            'message': '缺少message字段',
            'error_code': 'MISSING_FIELD'
        }), 400
    
    # 获取会话相关参数
    session_id = data.get('session_id')
    user_uuid = data.get('user_uuid')
    
    # 获取或创建conversation_id
    conversation_id = None
    if session_id:
        session_manager = SessionManager()
        conversation_id = session_manager.get_or_create_conversation_id(session_id)
    else:
        conversation_id = generate_conversation_id()
    
    # 构造流式请求体
    payload = {
        "conversation_id": conversation_id,
        "bot_id": BOT_ID,
        "user": user_uuid or 'anonymous_user',
        "query": user_input,
        "stream": True  # 启用流式
    }
    
    try:
        # 直接转发流式响应
        response = requests.post(BASE_URL, headers=headers, json=payload, stream=True)
        
        # 处理会话和存储（异步处理，不阻塞流式响应）
        def process_session_async():
            try:
                # 等待流式响应完成，收集完整响应内容
                full_response = b""
                for chunk in response.iter_content(chunk_size=1024):
                    full_response += chunk
                
                # 解析响应内容（这里简化处理，实际需要解析流式数据）
                response_text = "心理健康流式对话响应"
                
                # 处理会话和存储
                handle_session_and_storage(
                    user_uuid, 
                    session_id, 
                    user_input, 
                    response_text,
                    conversation_id
                )
            except Exception as e:
                logger.error(f"流式对话会话处理失败: {e}")
        
        # 设置响应头
        return Response(
            response.iter_content(chunk_size=1024),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Conversation-ID': conversation_id,
                'X-Session-ID': session_id or ''
            }
        )
        
    except Exception as e:
        logger.error(f"流式对话失败: {e}")
        return jsonify({
            'status': 'error',
            'message': '流式对话服务暂时不可用',
            'error_code': 'STREAM_ERROR'
        }), 500
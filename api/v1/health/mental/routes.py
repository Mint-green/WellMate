"""
心理健康对话路由

提供心理健康相关的文本对话接口，基于Mental Agent服务提供专业的心理支持和建议
"""

from flask import request, jsonify, Response, stream_with_context
import requests
import json
import os
import logging
import datetime
from . import mental_bp
from utils.jwt_utils import token_required, token_optional
from ..sessions.session_manager import session_manager

logger = logging.getLogger(__name__)

# === Mental Agent服务配置 ===
MENTAL_AGENT_BASE_URL = os.getenv("MENTAL_AGENT_BASE_URL", "http://localhost:6001")

# === Mental Agent接口端点 ===
HEALTH_ENDPOINT = "/health"
CHAT_ENDPOINT = "/chat"
CHAT_STREAM_ENDPOINT = "/chat/stream"
EMOTION_ANALYSIS_ENDPOINT = "/emotion-analysis"
TEXT_TO_SPEECH_ENDPOINT = "/text-to-speech"
SESSION_INFO_ENDPOINT = "/session/{session_id}/info"

# === 请求头 ===
headers = {
    "Content-Type": "application/json"
}

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
            session_info = session_manager.create_session(user_uuid, 'mental')
            if session_info:
                actual_session_id = session_info['session_id']
                is_new_session = True
                logger.info(f"创建新心理健康会话: {actual_session_id}")
            else:
                logger.error("创建新心理健康会话失败")
                return None, None, False
        else:
            # 检查会话是否存在且属于当前用户
            session_info = session_manager.get_session(actual_session_id)
            if not session_info or session_info['user_uuid'] != user_uuid:
                logger.warning(f"心理健康会话不存在或不属于当前用户: {actual_session_id}")
                # 创建新会话
                session_info = session_manager.create_session(user_uuid, 'mental')
                if session_info:
                    actual_session_id = session_info['session_id']
                    is_new_session = True
                    logger.info(f"创建新心理健康会话替代无效会话: {actual_session_id}")
                else:
                    logger.error("创建新心理健康会话失败")
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
        logger.error(f"处理心理健康会话存储异常: {e}")
        return actual_session_id, None, is_new_session

# === 调用Mental Agent服务 ===
def call_mental_agent(endpoint, payload=None, method='POST', timeout=60):
    """调用Mental Agent服务"""
    try:
        url = f"{MENTAL_AGENT_BASE_URL}{endpoint}"
        
        # 定义请求头
        headers = {
            'Content-Type': 'application/json'
        }
        
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code != 200:
            logger.error(f"Mental Agent服务调用失败: {response.status_code} - {response.text}")
            return None
        
        return response.json()
        
    except requests.exceptions.Timeout:
        logger.error(f"Mental Agent服务调用超时: {endpoint}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Mental Agent服务网络错误: {e}")
        return None
    except Exception as e:
        logger.error(f"Mental Agent服务调用异常: {e}")
        return None

# === 非流式对话接口 ===
@mental_bp.route('/chat', methods=['POST'])
@token_required
def mental_text_chat(current_user):
    """
    心理健康文本对话接口（非流式）
    
    接收用户输入，返回AI的心理健康建议和回复
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: text",
                "data": None
            }), 400
        
        user_input = data['text'].strip()
        if not user_input:
            return jsonify({
                "status": "error",
                "message": "输入文本不能为空",
                "data": None
            }), 400
        
        # 获取会话ID（可选）
        session_id = data.get('session_id')
        
        # 获取用户UUID（如果已登录）
        user_uuid = None
        if current_user and isinstance(current_user, dict) and 'uuid' in current_user:
            user_uuid = current_user['uuid']
        
        # 处理会话存储
        actual_session_id = session_id
        is_new_session = False
        
        if user_uuid and user_uuid != "anonymous_user":
            actual_session_id, conversation_id, is_new_session = handle_session_and_storage(
                user_uuid, session_id, user_input, None  # 先不存储AI回复
            )
            
            if not actual_session_id:
                logger.error("心理健康会话存储失败")
                return jsonify({
                    "status": "error",
                    "message": "心理健康会话管理失败，请重试",
                    "data": None
                }), 500
        
        # 调用Mental Agent聊天接口
        payload = {
            "message": user_input,
            "session_id": actual_session_id or "anonymous_session"
        }
        
        result = call_mental_agent(CHAT_ENDPOINT, payload)
        
        if not result or 'response' not in result:
            logger.error("Mental Agent聊天接口调用失败")
            return jsonify({
                "status": "error",
                "message": "心理健康服务暂时不可用，请稍后重试",
                "data": None
            }), 500
        
        ai_response = result.get('response', '')
        
        # 存储AI回复（仅在提供了user_uuid时）
        if user_uuid and user_uuid != "anonymous_user" and ai_response:
            session_manager.add_message(actual_session_id, 'assistant', ai_response, {
                'conversation_id': result.get('session_id', 'default'),
                'timestamp': datetime.datetime.now().isoformat()
            })

        # 构建响应数据
        response_data = {
            "response": ai_response,
            "user_input": user_input,
            "type": "mental",
            "session_id": actual_session_id,
            "is_new_session": is_new_session,
            "token_usage": result.get('token_usage', 0)
        }

        return jsonify({
            "status": "success",
            "message": "心理健康对话处理完成",
            "data": response_data
        }), 200
            
    except Exception as e:
        logger.error(f"心理健康对话接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": "系统内部错误",
            "data": None
        }), 500

# === 流式对话接口 ===
@mental_bp.route('/chat/stream', methods=['POST'])
@token_required
def mental_text_chat_stream(current_user):
    """
    心理健康文本对话接口（流式）
    
    接收用户输入，以流式方式返回AI的心理健康建议和回复
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: text",
                "data": None
            }), 400
        
        user_input = data['text'].strip()
        if not user_input:
            return jsonify({
                "status": "error",
                "message": "输入文本不能为空",
                "data": None
            }), 400
        
        # 获取会话ID（可选）
        session_id = data.get('session_id')
        
        # 获取用户UUID（如果已登录）
        user_uuid = None
        if current_user and isinstance(current_user, dict) and 'uuid' in current_user:
            user_uuid = current_user['uuid']
        
        # 处理会话存储
        actual_session_id = session_id
        is_new_session = False
        
        if user_uuid and user_uuid != "anonymous_user":
            actual_session_id, conversation_id, is_new_session = handle_session_and_storage(
                user_uuid, session_id, user_input, None  # 先不存储AI回复
            )
            
            if not actual_session_id:
                logger.error("心理健康会话存储失败")
                return jsonify({
                    "status": "error",
                    "message": "心理健康会话管理失败，请重试",
                    "data": None
                }), 500
        
        # 调用Mental Agent流式聊天接口
        payload = {
            "message": user_input,
            "session_id": actual_session_id or "anonymous_session"
        }
        
        def generate():
            try:
                url = f"{MENTAL_AGENT_BASE_URL}{CHAT_STREAM_ENDPOINT}"
                response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
                
                if response.status_code != 200:
                    logger.error(f"Mental Agent流式聊天接口调用失败: {response.status_code}")
                    error_data = json.dumps({
                        'status': 'error',
                        'message': '心理健康服务暂时不可用',
                        'data': None
                    })
                    yield f"data: {error_data}\n\n"
                    return
                
                ai_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line_str = line.decode('utf-8')
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]
                                if data_str.strip() == '[DONE]':
                                    break
                                
                                data_json = json.loads(data_str)
                                if data_json.get('type') == 'chunk':
                                    chunk_data = data_json.get('data', {})
                                    chunk = chunk_data.get('content', '')
                                    if chunk:
                                        ai_response += chunk
                                        chunk_data = json.dumps({
                                            'status': 'success',
                                            'message': '流式回复中',
                                            'data': {
                                                'chunk': chunk,
                                                'user_input': user_input,
                                                'type': 'mental',
                                                'session_id': actual_session_id,
                                                'is_new_session': is_new_session
                                            }
                                        })
                                        yield f"data: {chunk_data}\n\n"
                            
                        except json.JSONDecodeError:
                            continue
                        except Exception as e:
                            logger.error(f"流式数据处理异常: {e}")
                            continue
                
                # 存储完整的AI回复（仅在提供了user_uuid时）
                if user_uuid and user_uuid != "anonymous_user" and ai_response:
                    session_manager.add_message(actual_session_id, 'assistant', ai_response, {
                        'conversation_id': 'stream_conversation',
                        'timestamp': datetime.datetime.now().isoformat()
                    })
                
                complete_data = json.dumps({
                    'status': 'success',
                    'message': '流式回复完成',
                    'data': {
                        'complete': True,
                        'user_input': user_input,
                        'type': 'mental',
                        'session_id': actual_session_id,
                        'is_new_session': is_new_session
                    }
                })
                yield f"data: {complete_data}\n\n"
                
            except requests.exceptions.Timeout:
                logger.error("Mental Agent流式聊天接口调用超时")
                timeout_data = json.dumps({
                    'status': 'error',
                    'message': '服务响应超时',
                    'data': None
                })
                yield f"data: {timeout_data}\n\n"
            except requests.exceptions.RequestException as e:
                logger.error(f"网络请求失败: {e}")
                network_data = json.dumps({
                    'status': 'error',
                    'message': '网络连接失败',
                    'data': None
                })
                yield f"data: {network_data}\n\n"
            except Exception as e:
                logger.error(f"流式对话异常: {e}")
                error_data = json.dumps({
                    'status': 'error',
                    'message': '系统内部错误',
                    'data': None
                })
                yield f"data: {error_data}\n\n"
        
        return Response(stream_with_context(generate()), mimetype='text/plain')
            
    except Exception as e:
        logger.error(f"心理健康流式对话接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": "系统内部错误",
            "data": None
        }), 500

# === 情绪分析接口 ===
@mental_bp.route('/emotion-analysis', methods=['POST'])
@token_required
def mental_emotion_analysis(current_user):
    """
    情绪分析接口
    
    分析用户输入文本的情绪状态
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: text",
                "data": None
            }), 400
        
        user_input = data['text'].strip()
        if not user_input:
            return jsonify({
                "status": "error",
                "message": "输入文本不能为空",
                "data": None
            }), 400
        
        # 获取会话ID（可选）
        session_id = data.get('session_id', 'anonymous_session')
        
        # 调用Mental Agent情绪分析接口
        payload = {
            "text": user_input,
            "session_id": session_id
        }
        
        result = call_mental_agent(EMOTION_ANALYSIS_ENDPOINT, payload)
        
        if not result or not result.get('success'):
            logger.error("Mental Agent情绪分析接口调用失败")
            return jsonify({
                "status": "error",
                "message": "情绪分析服务暂时不可用，请稍后重试",
                "data": None
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "情绪分析完成",
            "data": {
                "emotion_analysis": result.get('emotion_analysis', {}),
                "input_text": user_input,
                "session_id": session_id,
                "token_usage": result.get('token_usage', 0)
            }
        }), 200
            
    except Exception as e:
        logger.error(f"情绪分析接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": "系统内部错误",
            "data": None
        }), 500

# === 文字转语音接口 ===
@mental_bp.route('/text-to-speech', methods=['POST'])
@token_required
def mental_text_to_speech(current_user):
    """
    心理健康文字转语音接口
    
    将文本转换为语音，用于心理健康对话的语音回复
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少必要参数: text",
                "data": None
            }), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({
                "status": "error",
                "message": "输入文本不能为空",
                "data": None
            }), 400
        
        # 调用Mental Agent文字转语音接口
        payload = {
            "input": text
        }
        
        result = call_mental_agent(TEXT_TO_SPEECH_ENDPOINT, payload)
        
        if not result or not result.get('success'):
            logger.error("Mental Agent文字转语音接口调用失败")
            return jsonify({
                "status": "error",
                "message": "语音合成服务暂时不可用",
                "data": None
            }), 500
        
        audio_data = result.get('audio_data', '')
        
        return jsonify({
            "status": "success",
            "message": "语音合成成功",
            "data": {
                "audio": audio_data,
                "text": text,
                "type": "mental"
            }
        }), 200
            
    except Exception as e:
        logger.error(f"文字转语音接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": "系统内部错误",
            "data": None
        }), 500

# === 会话管理接口 ===
@mental_bp.route('/session/<session_id>/info', methods=['GET'])
@token_required
def mental_session_info(current_user, session_id):
    """
    获取会话信息接口
    
    获取指定会话的详细信息
    """
    try:
        # 验证会话是否属于当前用户
        session_info = session_manager.get_session(session_id)
        if not session_info or session_info['user_uuid'] != current_user.uuid:
            return jsonify({
                "status": "error",
                "message": "会话不存在或无权限访问",
                "data": None
            }), 404
        
        # 调用Mental Agent会话信息接口
        endpoint = SESSION_INFO_ENDPOINT.replace('{session_id}', session_id)
        result = call_mental_agent(endpoint, method='GET')
        
        if not result or not result.get('success'):
            logger.error("Mental Agent会话信息接口调用失败")
            return jsonify({
                "status": "error",
                "message": "会话信息获取失败",
                "data": None
            }), 500
        
        return jsonify({
            "status": "success",
            "message": "会话信息获取成功",
            "data": {
                "session_info": result.get('session_info', {}),
                "session_id": session_id
            }
        }), 200
            
    except Exception as e:
        logger.error(f"会话信息接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": "系统内部错误",
            "data": None
        }), 500
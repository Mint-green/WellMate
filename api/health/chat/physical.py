from flask import Blueprint, request, jsonify
import requests
import json
import uuid
import os
from .. import health_response_decorator

# 创建健康物理对话相关的蓝图
physical_bp = Blueprint('healthphysical', __name__, url_prefix='/health/chat/physical')

# === Coze API 配置 ===
API_KEY = os.getenv("COZE_API_KEY", "pat_DyjwNAuK4thhVGMDE7WusSNFPFYwfiEEwYOs7WbOoZ9QJjNpXoQXPkNERk2Ld2aO")
BOT_ID = "7559087768224432170"  # 你的 Coze Agent ID
BASE_URL = "https://api.coze.cn/open_api/v2/chat"

# === 请求头 ===
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# === 生成唯一会话ID（单轮对话，每次生成新的） ===
def generate_conversation_id():
    return str(uuid.uuid4())

# === 发送对话函数 ===
def call_agent(user_input):
    # 生成新的会话ID（单轮对话）
    conversation_id = generate_conversation_id()
    
    # === 构造请求体 ===
    payload = {
        "conversation_id": conversation_id,
        "bot_id": BOT_ID,
        "user": "Miya",
        "query": user_input,
        "stream": False
    }

    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload))
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"Request failed: {response.status_code} - {response.text}",
                "data": None
            }

        res = response.json()
        messages = res.get("messages", [])

        # 从返回中提取 answer 类型的消息
        for msg in messages:
            if msg.get("type") == "answer":
                content = msg.get("content", "").strip()
                if content:
                    return {
                        "status": "success",
                        "message": "Physical chat completed",
                        "data": {
                            "response": content,
                            "conversation_id": conversation_id
                        }
                    }

        # 如果没有找到有效回复
        return {
            "status": "warning",
            "message": "Agent didn't return a message. This may happen if the model timed out or your input triggered a filter.",
            "data": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Network error: {e}",
            "data": None
        }
    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": f"Response JSON parse error: {response.text[:200]}",
            "data": None
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {e}",
            "data": None
        }

# === 健康物理对话接口（单轮对话版本） ===
@physical_bp.route('', methods=['POST'])
@health_response_decorator
def physical_chat():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return {
                "status": "error",
                "message": "Invalid JSON data",
                "data": None
            }
        
        user_input = data.get('message')
        if not user_input:
            return {
                "status": "error",
                "message": "Missing 'message' field in request",
                "data": None
            }
        
        # 调用Coze Agent
        result = call_agent(user_input)
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error in physical chat: {e}",
            "data": None
        }

# === 健康物理对话接口（流式版本） ===
@physical_bp.route('/stream', methods=['POST'])
def physical_chat_stream():
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Invalid JSON data"
            }), 400
        
        user_input = data.get('message')
        if not user_input:
            return jsonify({
                "status": "error",
                "message": "Missing 'message' field in request"
            }), 400
        
        # 生成新的会话ID
        conversation_id = generate_conversation_id()
        
        # === 构造请求体 ===
        payload = {
            "conversation_id": conversation_id,
            "bot_id": BOT_ID,
            "user": "Miya",
            "query": user_input,
            "stream": True  # 启用流式
        }
        
        # 直接转发流式响应
        response = requests.post(BASE_URL, headers=headers, json=payload, stream=True)
        
        # 设置响应头
        return response.raw, 200, {
            'Content-Type': 'text/event-stream',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        }
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error in physical chat stream: {e}"
        }), 500
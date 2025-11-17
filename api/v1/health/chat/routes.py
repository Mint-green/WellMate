"""
健康对话路由

提供健康相关的文本对话接口
"""

from flask import request, jsonify, Response, stream_with_context
import time
from . import chat_bp

# 健康文本对话接口（非流式版本）
@chat_bp.route('/text', methods=['POST'])
def text_chat():
    """健康文本对话"""
    data = request.get_json()
    
    return jsonify({
        'status': 'success',
        'message': '健康对话处理完成',
        'data': {
            'response': '这是健康对话的响应',
            'user_input': data.get('message', '')
        }
    })

# 健康文本对话接口（流式版本）
@chat_bp.route('/text/stream', methods=['POST'])
def text_chat_stream():
    """健康文本对话（流式）"""
    data = request.get_json()
    
    @stream_with_context
    def generate():
        # 发送初始状态
        yield 'event: status\n'
        yield 'data: {"status": "success", "message": "流式对话开始"}\n\n'
        
        # 模拟流式数据输出
        for i in range(3):
            time.sleep(1)  # 模拟处理时间
            
            # 发送事件数据
            yield 'event: message\n'
            message = data.get('message', '')
            yield f'data: {{"content": "流式响应部分 {i+1}", "user_input": "{message}"}}\n\n'
        
        # 发送结束事件
        yield 'event: complete\n'
        yield 'data: {"status": "success", "message": "流式对话完成"}\n\n'
    
    return Response(generate(), mimetype='text/event-stream')
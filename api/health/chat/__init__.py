from flask import Blueprint, Response, stream_with_context
import time

# 创建健康对话相关的蓝图
chat_bp = Blueprint('healthchat', __name__, url_prefix='/health/chat')

# 健康文本对话接口（非流式版本）
from .. import health_response_decorator
@chat_bp.route('/text', methods=['POST'])
@health_response_decorator
def text_chat():
    # 这里可以添加文本对话的逻辑
    return {
        'status': 'success',
        'message': 'Processing text chat request',
        'data': None
    }

# 健康文本对话接口（SSE流式版本）
@chat_bp.route('/text/stream', methods=['POST'])
def text_chat_stream():
    @stream_with_context
    def generate():    
        # 发送初始状态
        yield 'event: status\n'
        yield 'data: {"status": "success", "message": "Stream started"}\n\n'
        
        # 模拟流式数据输出，实际应用中可以根据模型输出或数据处理进度生成内容
        for i in range(3):
            time.sleep(1)  # 模拟处理时间
            
            # 发送事件数据
            yield 'event: message\n'
            yield f'data: {{"content": "Stream response part {i+1}"}}\n\n'
        
        # 发送结束事件
        yield 'event: complete\n'
        yield 'data: {"status": "success", "message": "Stream completed"}\n\n'
    
    # 返回流式响应，设置适当的Content-Type
    return Response(generate(), mimetype='text/event-stream')

# 导入物理对话蓝图
from .physical import physical_bp
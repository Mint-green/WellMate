import json
import ssl
import uuid
from datetime import datetime
import os
from typing import Optional, AsyncGenerator, Dict, Any, List
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, HTTPException, Query, Path, Depends, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# 假设从配置模块导入服务器配置
from config import SERVER_CONFIG
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("api_server")

# 假设从coze客户端模块导入
from coze_api_client import CozeAPIClient
from coze_tts_client import CozeTTSClient  # 新增TTS客户端导入

# 从coze_tts_client获取默认voice_id（使用测试代码中的默认值）
from coze_tts_client import TEST_VOICE_ID  # 新增导入默认音色ID

# 新增：导入情绪分析功能
from coze_emotiontag import EmotionAnalyzer

# 全局应用状态存储
app_state: Dict[str, Any] = {}

# ==================== 应用生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("正在初始化Coze聊天机器人API服务器...")
    
    try:
        # 初始化Coze聊天客户端
        coze_chat_client = CozeAPIClient(debug=SERVER_CONFIG.get("debug", False))
        
        # 初始化Coze TTS客户端
        coze_tts_client = CozeTTSClient(debug=SERVER_CONFIG.get("debug", False))
        
        # 新增：初始化情绪分析器
        emotion_analyzer = EmotionAnalyzer()
        
        # 保存到应用状态
        app_state["coze_chat_client"] = coze_chat_client  # 重命名为明确的聊天客户端
        app_state["coze_tts_client"] = coze_tts_client    # 新增TTS客户端
        app_state["emotion_analyzer"] = emotion_analyzer   # 新增情绪分析器
        app_state["session_map"] = {}  # session_id -> 会话信息映射
        app_state["conv_map"] = {}     # conversation_id -> session_id映射（反向查找）
        
        logger.info("Coze聊天机器人API服务器初始化完成")
        logger.info(f"当前Bot ID: {coze_chat_client.bot_id}")
        logger.info(f"默认TTS音色ID: {TEST_VOICE_ID}")  # 打印默认音色ID
        logger.info(f"情绪分析功能: 已启用")  # 新增日志
        logger.info(f"服务器配置: {SERVER_CONFIG}")
        
        yield
        
        # 关闭时清理
        logger.info("正在关闭Coze聊天机器人API服务器...")
        app_state.clear()
        logger.info("Coze聊天机器人API服务器已关闭")
        
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}", exc_info=True)
        raise

# 初始化FastAPI应用
app = FastAPI(
    title="Coze聊天机器人API服务",
    description="提供聊天、文本转语音和情绪分析功能的API服务",  # 更新描述
    version="1.3.0",  # 更新版本号
    lifespan=lifespan
)

# ==================== Pydantic模型（数据校验）====================
"""聊天消息请求（新增conversation_id参数）"""
class ChatMessageRequest(BaseModel):
    """聊天消息请求（新增conversation_id参数）"""
    user_id: Optional[str] = Field(default=None, description="用户ID（可选，默认自动生成）")
    message: str = Field(..., description="用户消息内容（必填）", min_length=1)
    session_id: Optional[str] = Field(default=None, description="会话ID（可选，默认自动生成）")
    conversation_id: Optional[str] = Field(default=None, description="Coze会话ID（可选，传入则续传该会话）")

"""同步聊天响应"""
class ChatMessageResponse(BaseModel):
    """同步聊天响应"""
    response: str = Field(..., description="机器人完整回复")
    session_id: str = Field(..., description="会话ID")
    message_id: str = Field(..., description="消息唯一ID")
    timestamp: str = Field(..., description="响应时间戳")
    conversation_id: str = Field(..., description="Coze会话ID（用于后续续传）")

"""绑定会话ID请求"""
class BindConversationRequest(BaseModel):
    """绑定会话ID请求"""
    conversation_id: str = Field(..., description="Coze会话ID（从聊天响应中获取）")

# -------------------- 新增TTS相关Pydantic模型 --------------------
"""文本转语音请求（匹配Coze官方API，使用默认voice_id）"""
class TextToSpeechRequest(BaseModel):
    """文本转语音请求（匹配Coze官方API）"""
    input: str = Field(..., description="合成语音的文本（必填，UTF-8编码，≤1024字节）", min_length=1)
    voice_id: Optional[str] = Field(
        default=TEST_VOICE_ID,  # 使用默认音色ID
        description=f"音色ID（可选，默认使用: {TEST_VOICE_ID}，需通过Coze音色列表API获取可用值）"
    )
    emotion: Optional[str] = Field(
        default=None,
        description="情感类型（可选，仅多情感音色支持，枚举值：happy/sad/angry/surprised/fear/hate/excited/coldness/neutral）"
    )
    emotion_scale: Optional[float] = Field(
        default=4.0,
        ge=1.0,
        le=5.0,
        description="情感强度（可选，1.0~5.0，数值越高情感越强烈，默认4.0）"
    )

"""文本转语音响应元数据（可选，用于同步返回场景）"""
class TextToSpeechResponse(BaseModel):
    """文本转语音响应元数据（可选，用于同步返回场景）"""
    task_id: str = Field(..., description="语音生成任务ID（由服务端生成）")
    voice_id: str = Field(..., description="使用的音色ID")
    text_length: int = Field(..., description="输入文本UTF-8字节长度")
    audio_format: str = Field(default="mp3", description="音频格式（Coze官方默认）")
    timestamp: str = Field(..., description="响应时间戳")

# -------------------- 新增情绪分析相关Pydantic模型 --------------------
"""情绪分析请求"""
class EmotionAnalysisRequest(BaseModel):
    """情绪分析请求"""
    text: str = Field(..., description="要分析情绪的文本内容", min_length=1)
    user_id: Optional[str] = Field(default=None, description="用户ID（可选，默认自动生成）")

"""情绪分析响应"""
class EmotionAnalysisResponse(BaseModel):
    """情绪分析响应"""
    success: bool = Field(..., description="分析是否成功")
    input_text: str = Field(..., description="输入的文本")
    emotion_analysis: Optional[str] = Field(None, description="情绪分析结果")
    error: Optional[str] = Field(None, description="错误信息（如果分析失败）")
    status: Optional[str] = Field(None, description="分析状态")
    token_usage: Optional[int] = Field(None, description="Token使用量")
    timestamp: str = Field(..., description="响应时间戳")

# ==================== 核心工具函数 ====================
"""更新会话映射（双向绑定）"""
def _update_session_mapping(session_id: str, user_id: str, conversation_id: str):
    """更新会话映射（双向绑定）"""
    # 移除旧的反向映射（如果该conversation_id已绑定其他session）
    old_session_id = app_state["conv_map"].get(conversation_id)
    if old_session_id and old_session_id != session_id:
        del app_state["session_map"][old_session_id]
    
    # 更新正向和反向映射
    app_state["session_map"][session_id] = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "last_activity": datetime.now().isoformat()
    }
    app_state["conv_map"][conversation_id] = session_id

"""通过session_id获取绑定的conversation_id"""
def _get_conversation_id_by_session(session_id: str) -> Optional[str]:
    """通过session_id获取绑定的conversation_id"""
    session_info = app_state["session_map"].get(session_id)
    return session_info["conversation_id"] if session_info else None

# -------------------- 新增TTS工具函数 --------------------
"""生成唯一的TTS任务ID"""
def _generate_tts_task_id() -> str:
    """生成唯一的TTS任务ID"""
    return f"tts_task_{uuid.uuid4().hex[:16]}"

# ==================== API路由 ====================
"""根路径健康提示"""
@app.get("/")
async def root():
    """根路径健康提示"""
    return {
        "message": "Coze聊天机器人API服务正在运行",
        "version": "1.3.0",  # 更新版本号
        "status": "healthy",
        "docs": "/docs",  # Swagger文档地址
        "features": ["同步聊天", "流式聊天", "会话续传", "会话绑定", "上下文管理", "文本转语音", "情绪分析"]  # 新增情绪分析功能
    }

"""健康检查接口"""
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "coze_chat_client_status": "initialized" if app_state.get("coze_chat_client") else "uninitialized",
        "coze_tts_client_status": "initialized" if app_state.get("coze_tts_client") else "uninitialized",
        "emotion_analyzer_status": "initialized" if app_state.get("emotion_analyzer") else "uninitialized",  # 新增情绪分析器状态
        "active_sessions": len(app_state.get("session_map", {})),
        "active_conversations": len(app_state.get("conv_map", {})),
        "tts_support": "enabled" if app_state.get("coze_tts_client") else "disabled",
        "emotion_analysis_support": "enabled" if app_state.get("emotion_analyzer") else "disabled",  # 新增情绪分析支持状态
        "default_voice_id": TEST_VOICE_ID  # 新增默认音色ID展示
    }

"""
    同步聊天接口（支持会话续传）
    - 支持传入 conversation_id 续传已有会话
    - 支持传入 session_id 关联已有会话
    - 未传入则自动生成新会话
    """
@app.post("/chat", response_model=ChatMessageResponse)
async def chat(request: ChatMessageRequest):
    """
    同步聊天接口（支持会话续传）
    - 支持传入 conversation_id 续传已有会话
    - 支持传入 session_id 关联已有会话
    - 未传入则自动生成新会话
    """
    try:
        # 获取客户端实例
        coze_chat_client = app_state.get("coze_chat_client")
        if not coze_chat_client:
            raise HTTPException(status_code=500, detail="Coze聊天客户端未初始化")
        
        # 1. 处理用户ID和会话ID
        user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        message_id = f"msg_{uuid.uuid4().hex[:16]}"
        
        # 2. 处理会话续传逻辑（优先级：传入的conversation_id > session_id绑定的conversation_id > 新建）
        target_conv_id = None
        if request.conversation_id:
            # 传入了conversation_id，直接绑定
            target_conv_id = request.conversation_id
            coze_chat_client.set_conversation_id(target_conv_id)
            logger.info(f"同步聊天 - 手动传入会话ID: {target_conv_id[:15]}...")
        elif session_id in app_state["session_map"]:
            # 已有session_id绑定的conversation_id，自动续传
            target_conv_id = _get_conversation_id_by_session(session_id)
            if target_conv_id:
                coze_chat_client.set_conversation_id(target_conv_id)
                logger.info(f"同步聊天 - 续传session绑定会话ID: {target_conv_id[:15]}...")
        
        logger.info(f"同步聊天请求 - session_id: {session_id}, user_id: {user_id}, message: {request.message[:50]}...")
        
        # 3. 调用Coze客户端（同步模式）
        response_text = coze_chat_client.send_message_sync(message=request.message)
        
        # 4. 获取实际使用的conversation_id（可能是新建或传入的）
        actual_conv_id = coze_chat_client.get_current_conversation_id()
        if not actual_conv_id:
            raise Exception("Coze API未返回有效的conversation_id")
        
        # 5. 更新会话映射（双向绑定）
        _update_session_mapping(session_id, user_id, actual_conv_id)
        
        logger.info(f"同步聊天响应 - session_id: {session_id}, conv_id: {actual_conv_id[:15]}..., response: {response_text[:50]}...")
        
        return ChatMessageResponse(
            response=response_text,
            session_id=session_id,
            message_id=message_id,
            timestamp=datetime.now().isoformat(),
            conversation_id=actual_conv_id  # 返回conversation_id，供后续续传
        )

    except ValueError as ve:
        # 捕获无效conversation_id的异常
        logger.error(f"同步聊天参数错误: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(ve)}")
    except Exception as e:
        logger.error(f"同步聊天处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"同步聊天失败: {str(e)}")

"""
    流式聊天接口（SSE格式，支持会话续传）
    - 支持传入 conversation_id 续传已有会话
    - 实时返回回复片段
    - 响应格式：data: {"type": "chunk"/"complete"/"error", ...}
    """
@app.post("/chat/stream")
async def chat_stream(request: ChatMessageRequest):
    """
    流式聊天接口（SSE格式，支持会话续传）
    - 支持传入 conversation_id 续传已有会话
    - 实时返回回复片段
    - 响应格式：data: {"type": "chunk"/"complete"/"error", ...}
    """
    try:
        # 1. 处理ID生成
        user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
        session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
        message_id = f"msg_{uuid.uuid4().hex[:16]}"
        
        # 2. 预处理会话续传参数（供生成器使用）
        target_conv_id = request.conversation_id
        use_existing_session = session_id in app_state["session_map"]
        
        logger.info(f"流式聊天请求 - session_id: {session_id}, user_id: {user_id}, conv_id: {target_conv_id[:15] if target_conv_id else '新建'}, message: {request.message[:50]}...")
        
        async def stream_generator():
            """流式响应生成器（异步迭代）"""
            try:
                coze_chat_client = app_state.get("coze_chat_client")
                if not coze_chat_client:
                    raise Exception("Coze聊天客户端未初始化")
                
                # 3. 绑定会话ID（续传逻辑）
                actual_conv_id = None

                if target_conv_id:
                    coze_chat_client.set_conversation_id(target_conv_id)
                    actual_conv_id = target_conv_id
                    logger.info(f"流式聊天 - 手动绑定会话ID: {actual_conv_id[:15]}...")
                elif use_existing_session:
                    actual_conv_id = _get_conversation_id_by_session(session_id)
                    if actual_conv_id:
                        coze_chat_client.set_conversation_id(actual_conv_id)
                        logger.info(f"流式聊天 - 续传会话ID: {actual_conv_id[:15]}...")
                
                # 4. 初始化会话映射（如果是新会话）
                if not actual_conv_id:
                    app_state["session_map"][session_id] = {
                        "user_id": user_id,
                        "conversation_id": None,
                        "last_activity": datetime.now().isoformat()
                    }
                
                chunk_count = 0
                full_content = ""
                
                # 5. 迭代Coze客户端的流式生成器
                for stream_data in coze_chat_client.send_message_stream(message=request.message):
                    stream_type = stream_data.get("type")
                    
                    # 内容块：实时返回
                    if stream_type == "chunk":
                        chunk_count += 1
                        content = stream_data.get("content", "")
                        full_content += content
                        
                        # 构建SSE响应数据
                        response_chunk = {
                            "type": "chunk",
                            "data": {
                                "content": content,
                                "session_id": session_id,
                                "message_id": message_id,
                                "chunk_index": chunk_count,
                                "conversation_id": stream_data.get("conversation_id"),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        yield f"data: {json.dumps(response_chunk, ensure_ascii=False)}\n\n"
                        
                        # 控制流速（可选）
                        import asyncio
                        await asyncio.sleep(0.03)
                    
                    # 完成标识：返回汇总信息+更新会话映射
                    elif stream_type == "complete":
                        actual_conv_id = stream_data.get("conversation_id")
                        if not actual_conv_id:
                            raise Exception("流式响应未返回conversation_id")
                        
                        # 更新双向会话映射
                        _update_session_mapping(session_id, user_id, actual_conv_id)
                        
                        complete_data = {
                            "type": "complete",
                            "data": {
                                "session_id": session_id,
                                "message_id": message_id,
                                "total_chunks": chunk_count,
                                "full_content": full_content,
                                "conversation_id": actual_conv_id,  # 返回供后续续传
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        logger.info(f"流式聊天完成 - session_id: {session_id}, conv_id: {actual_conv_id[:15]}..., total_chunks: {chunk_count}")
                        yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                        
                    # 错误信息：返回错误
                    elif stream_type == "error":
                        error_data = {
                            "type": "error",
                            "data": {
                                "message": stream_data.get("message", "未知错误"),
                                "session_id": session_id,
                                "message_id": message_id,
                                "conversation_id": stream_data.get("conversation_id"),
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                        logger.error(f"流式聊天错误 - session_id: {session_id}, error: {stream_data.get('message')}")
                        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                        break
                
            except ValueError as ve:
                # 无效conversation_id异常
                error_msg = f"会话ID参数错误: {str(ve)}"
                error_data = {
                    "type": "error",
                    "data": {
                        "message": error_msg,
                        "session_id": session_id,
                        "message_id": message_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            except Exception as gen_error:
                error_msg = f"流式生成器异常: {str(gen_error)}"
                logger.error(error_msg, exc_info=True)
                error_data = {
                    "type": "error",
                    "data": {
                        "message": error_msg,
                        "session_id": session_id,
                        "message_id": message_id,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        # 6. 返回SSE流式响应
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用Nginx缓冲（可选）
                "Content-Encoding": "identity"
            }
        )
        
    except ValueError as ve:
        logger.error(f"流式聊天参数错误: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(ve)}")
    except Exception as e:
        logger.error(f"流式聊天处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"流式聊天失败: {str(e)}")

"""
    绑定会话ID（手动关联session_id和conversation_id）
    - 用于已有conversation_id时，绑定到指定session_id
    - 绑定后，该session_id的后续聊天会自动续传该conversation_id
    """
@app.post("/session/{session_id}/bind")
async def bind_conversation(session_id: str, request: BindConversationRequest):
    """
    绑定会话ID（手动关联session_id和conversation_id）
    - 用于已有conversation_id时，绑定到指定session_id
    - 绑定后，该session_id的后续聊天会自动续传该conversation_id
    """
    try:
        coze_chat_client = app_state.get("coze_chat_client")
        if not coze_chat_client:
            raise HTTPException(status_code=500, detail="Coze聊天客户端未初始化")
        
        conversation_id = request.conversation_id
        # 校验conversation_id有效性（调用coze_client的校验逻辑）
        coze_chat_client.set_conversation_id(conversation_id)
        
        # 获取用户ID（如果session已存在则复用，否则自动生成）
        user_id = app_state["session_map"].get(session_id, {}).get("user_id") or f"user_{uuid.uuid4().hex[:8]}"
        
        # 更新双向映射
        _update_session_mapping(session_id, user_id, conversation_id)
        
        logger.info(f"会话绑定成功 - session_id: {session_id}, conversation_id: {conversation_id[:15]}...")
        
        return {
            "message": "会话ID绑定成功",
            "session_id": session_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as ve:
        logger.error(f"会话绑定失败: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"绑定失败: {str(ve)}")
    except Exception as e:
        logger.error(f"会话绑定失败 - session_id: {session_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"绑定失败: {str(e)}")

"""
    清除指定会话（重置上下文）
    - 同时清除session_id与conversation_id的绑定关系
    """
@app.post("/session/{session_id}/clear")
async def clear_session(session_id: str):
    """
    清除指定会话（重置上下文）
    - 同时清除session_id与conversation_id的绑定关系
    """
    try:
        coze_chat_client = app_state.get("coze_chat_client")
        if not coze_chat_client:
            raise HTTPException(status_code=500, detail="Coze聊天客户端未初始化")
        
        # 1. 清除客户端会话上下文
        coze_chat_client.clear_conversation()
        
        # 2. 清除双向映射
        session_info = app_state["session_map"].get(session_id)
        if session_info:
            conversation_id = session_info["conversation_id"]
            if conversation_id in app_state["conv_map"]:
                del app_state["conv_map"][conversation_id]
            del app_state["session_map"][session_id]
            logger.info(f"会话清除成功 - session_id: {session_id}, conv_id: {conversation_id[:15] if conversation_id else '无'}")
        else:
            logger.warning(f"会话清除 - session_id: {session_id} 不存在")
        
        return {
            "message": "会话已成功清除（上下文已重置）",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清除会话失败 - session_id: {session_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清除会话失败: {str(e)}")

"""
    获取会话详细信息
    - 返回session_id、user_id、conversation_id、最后活动时间
    """
@app.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """
    获取会话详细信息
    - 返回session_id、user_id、conversation_id、最后活动时间
    """
    try:
        session_info = app_state["session_map"].get(session_id)
        if not session_info:
            raise HTTPException(status_code=404, detail=f"会话不存在 - session_id: {session_id}")
        
        return {
            "session_id": session_id,
            "info": {
                "user_id": session_info["user_id"],
                "conversation_id": session_info["conversation_id"],
                "last_activity": session_info["last_activity"],
                "status": "active"
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话信息失败 - session_id: {session_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话信息失败: {str(e)}")

"""
    通过conversation_id查询绑定的session_id
    - 反向查找：已知conversation_id，获取对应的会话信息
    """
@app.get("/conversation/{conversation_id}/session")
async def get_session_by_conversation(conversation_id: str):
    """
    通过conversation_id查询绑定的session_id
    - 反向查找：已知conversation_id，获取对应的会话信息
    """
    try:
        session_id = app_state["conv_map"].get(conversation_id)
        if not session_id:
            raise HTTPException(status_code=404, detail=f"未找到绑定的会话 - conversation_id: {conversation_id}")
        
        session_info = app_state["session_map"][session_id]
        return {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "session_info": {
                "user_id": session_info["user_id"],
                "last_activity": session_info["last_activity"]
            },
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询会话失败 - conv_id: {conversation_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询会话失败: {str(e)}")

"""
    列出当前活跃的会话（分页）
    - 仅返回基础信息，不包含历史消息
    """
@app.get("/sessions")
async def list_sessions(limit: int = Query(10, ge=1, le=50), offset: int = Query(0, ge=0)):
    """
    列出当前活跃的会话（分页）
    - 仅返回基础信息，不包含历史消息
    """
    try:
        session_list = list(app_state["session_map"].items())[offset:offset+limit]
        return {
            "total": len(app_state["session_map"]),
            "limit": limit,
            "offset": offset,
            "sessions": [
                {
                    "session_id": sid,
                    "user_id": info["user_id"],
                    "conversation_id": info["conversation_id"],
                    "last_activity": info["last_activity"]
                } for sid, info in session_list
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"列出会话失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"列出会话失败: {str(e)}")

# -------------------- 新增文本转语音API路由 --------------------
"""
    调用Coze官方文本转语音API，流式返回MP3音频
    - 文本限制：UTF-8编码≤1024字节，支持中英文
    - 情感配置：仅多情感音色支持emotion参数，需参考Coze音色列表
    - 响应格式：MP3音频流，前端可直接播放或下载
    """
@app.post("/text-to-speech", summary="文本转语音接口（Coze官方集成）")
async def text_to_speech(request: TextToSpeechRequest):
    """
    调用Coze官方文本转语音API，流式返回MP3音频
    - 文本限制：UTF-8编码≤1024字节，支持中英文
    - 情感配置：仅多情感音色支持emotion参数，需参考Coze音色列表
    - 响应格式：MP3音频流，前端可直接播放或下载
    """
    try:
        # 1. 校验Coze TTS客户端
        coze_tts_client = app_state.get("coze_tts_client")
        if not coze_tts_client:
            raise HTTPException(status_code=500, detail="Coze TTS客户端未初始化，无法调用TTS服务")
        
        # 2. 校验文本字节长度（UTF-8编码）
        input_bytes = request.input.encode('utf-8')
        if len(input_bytes) > 1024:
            raise HTTPException(
                status_code=400,
                detail=f"输入文本过长：UTF-8编码后{len(input_bytes)}字节，最大支持1024字节"
            )
        
        # 3. 生成任务ID
        task_id = _generate_tts_task_id()
        logger.info(f"TTS请求 - task_id: {task_id}, voice_id: {request.voice_id[:15]}..., text_length: {len(input_bytes)}字节")
        
        # 4. 调用Coze TTS客户端的text_to_speech方法（流式获取音频）
        audio_stream = coze_tts_client.text_to_speech(
            input=request.input,
            voice_id=request.voice_id,  # 使用请求中的voice_id（默认已设置为TEST_VOICE_ID）
            emotion=request.emotion,
            emotion_scale=request.emotion_scale
        )
        
        # 5. 构建流式响应（返回MP3音频）
        return StreamingResponse(
            audio_stream,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=\"tts_{task_id}.mp3\"",
                "X-Task-Id": task_id,
                "X-Voice-Id": request.voice_id,
                "X-Text-Length": str(len(input_bytes)),
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    
    except ValueError as ve:
        logger.error(f"TTS参数错误 - task_id: {task_id if 'task_id' in locals() else 'unknown'}, error: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"参数错误：{str(ve)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS处理失败 - task_id: {task_id if 'task_id' in locals() else 'unknown'}, error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文本转语音失败：{str(e)}")

# -------------------- 新增情绪分析API路由 --------------------
"""
    情绪分析接口
    - 调用Coze API为输入文本打上情绪标签
    - 返回情绪分析结果和详细信息
    """
@app.post("/emotion-analysis", response_model=EmotionAnalysisResponse, summary="情绪分析接口")
async def emotion_analysis(request: EmotionAnalysisRequest):
    """
    情绪分析接口
    - 调用Coze API为输入文本打上情绪标签
    - 返回情绪分析结果和详细信息
    """
    try:
        # 1. 校验情绪分析器
        emotion_analyzer = app_state.get("emotion_analyzer")
        if not emotion_analyzer:
            raise HTTPException(status_code=500, detail="情绪分析器未初始化，无法调用情绪分析服务")
        
        # 2. 生成用户ID（如果未提供）
        user_id = request.user_id or f"user_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"情绪分析请求 - user_id: {user_id}, text: {request.text[:50]}...")
        
        # 3. 调用情绪分析器
        result = emotion_analyzer.analyze_emotion(request.text, user_id)
        
        logger.info(f"情绪分析响应 - user_id: {user_id}, success: {result['success']}")
        
        # 4. 构建响应
        return EmotionAnalysisResponse(
            success=result['success'],
            input_text=result['input_text'],
            emotion_analysis=result.get('emotion_analysis'),
            error=result.get('error'),
            status=result.get('status'),
            token_usage=result.get('token_usage'),
            timestamp=datetime.now().isoformat()
        )
    
    except ValueError as ve:
        logger.error(f"情绪分析参数错误: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"参数错误: {str(ve)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"情绪分析处理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"情绪分析失败: {str(e)}")

# ==================== 全局错误处理 ====================
"""404错误处理"""
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404错误处理"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "资源未找到",
            "status_code": 404,
            "message": f"路径 {request.url.path} 不存在",
            "timestamp": datetime.now().isoformat()
        }
    )

"""500错误处理"""
@app.exception_handler(500)
async def server_error_handler(request, exc):
    """500错误处理"""
    logger.error(f"服务器内部错误 - 路径: {request.url.path}, 错误: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "status_code": 500,
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

# ==================== 启动函数 ====================
if __name__ == "__main__":
    import uvicorn
    
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 启动服务器（从配置读取参数）
    uvicorn.run(
        "api_server:app",
        host=SERVER_CONFIG.get("host", "0.0.0.0"),
        port=SERVER_CONFIG.get("port", 6001),
        reload=SERVER_CONFIG.get("debug", False),
        log_level=SERVER_CONFIG.get("log_level", "info"),
        access_log=True
    )
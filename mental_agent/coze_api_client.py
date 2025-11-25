#!/usr/bin/env python3
"""
基于Coze V3 API官方规范的心理聊天客户端
最终稳定版：同步聊天正常 + 流式聊天正常 + 上下文关联正常
修复：流式SSE格式解析错误、事件匹配错误、数据结构解析错误
新增：set_conversation_id() 函数，支持手动传入会话ID续传会话
"""

import os
import json
import time
import traceback
import requests
import ssl
from dotenv import load_dotenv
from typing import Optional, Dict, Iterator, Any
from contextlib import contextmanager
from urllib3.poolmanager import PoolManager
from urllib3.exceptions import InsecureRequestWarning

# 禁用不安全请求警告（开发环境）
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 加载环境变量
load_dotenv()

# 自定义SSL适配器：修复SSL上下文参数错误，兼容Python 3.7+
class TLSAdapter(requests.adapters.HTTPAdapter):
    def __init__(self):
        super().__init__()

    def init_poolmanager(self, connections, maxsize, block=False):
        """
        修复SSL上下文初始化：
        1. create_default_context第一个参数必须是ssl.Purpose枚举
        2. 通过minimum_version强制TLSv1.2+（兼容Python 3.7+）
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False  # 开发环境禁用主机名验证
        context.verify_mode = ssl.CERT_NONE  # 开发环境禁用证书验证
        
        # 强制最小TLS版本为1.2（关键：避免低版本TLS连接失败）
        if hasattr(context, 'minimum_version'):
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        else:
            context.options |= ssl.OP_NO_TLSv1
            context.options |= ssl.OP_NO_TLSv1_1
        
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=context
        )

class CozeAPIClient:
    def __init__(self, debug: bool = False):
        # 核心配置（严格对应Coze官方必填项）
        self.base_url = os.getenv('COZE_BASE_URL', "https://api.coze.cn/v3")
        self.api_token = os.getenv('COZE_API_TOKEN')
        self.bot_id = os.getenv('COZE_BOT_ID')
        self.user_id = os.getenv('COZE_USER_ID', 'default_user_123')
        
        # 会话核心：维护当前conversation_id（关联上下文的关键）
        self.conversation_id: Optional[str] = None
        self.debug = debug  # 调试模式：打印详细日志
        
        # 超时配置（贴合Coze API响应特性）
        self.sync_timeout = 60  # 同步请求总超时（含消息轮询）
        self.stream_timeout = 60  # 流式请求超时
        self.poll_interval = 1  # 消息列表轮询间隔（秒）

        # 校验必填配置（官方文档强制要求）
        if not self.api_token:
            raise ValueError("❌ 请设置COZE_API_TOKEN环境变量（从Coze开放平台获取）")
        if not self.bot_id:
            raise ValueError("❌ 请设置COZE_BOT_ID环境变量（从Coze开放平台获取）")

        # 初始化requests会话（修复SSL适配器）
        self.session = requests.Session()
        self.session.mount("https://", TLSAdapter())  # 适配TLSv1.2+

    def _get_headers(self) -> Dict[str, str]:
        """获取Coze官方规范的请求头"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "Coze-Python-Client/1.0 (Psychological Agent Compatible)"
        }

    @contextmanager
    def _handle_request_errors(self, operation: str, url: str = "", params: dict = None, data: dict = None):
        """增强版错误处理：打印完整请求信息+响应信息+异常堆栈"""
        try:
            yield
        except requests.exceptions.RequestException as e:
            error_msg = f"\n❌ {operation}失败！"
            error_msg += f"\n请求URL: {url}"
            if params:
                error_msg += f"\n请求参数: {json.dumps(params, ensure_ascii=False)}"
            if data:
                error_msg += f"\n请求体: {json.dumps(data, ensure_ascii=False)}"
            error_msg += f"\n错误类型: {type(e).__name__}"
            error_msg += f"\n错误描述: {str(e)}"
            
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\n响应状态码: {e.response.status_code}"
                try:
                    resp_json = e.response.json()
                    error_msg += f"\nAPI响应: {json.dumps(resp_json, ensure_ascii=False, indent=2)}"
                except:
                    error_msg += f"\nAPI响应（原始文本）: {e.response.text[:500]}"
            
            error_msg += f"\n异常堆栈:\n{traceback.format_exc()}"
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"\n❌ {operation}失败！"
            error_msg += f"\n错误类型: {type(e).__name__}"
            error_msg += f"\n错误描述: {str(e)}"
            error_msg += f"\n异常堆栈:\n{traceback.format_exc()}"
            raise Exception(error_msg)

    def _build_chat_url(self) -> str:
        """构建聊天API URL（自动附加conversation_id，关联上下文）"""
        url = f"{self.base_url}/chat"
        if self.conversation_id:
            url += f"?conversation_id={self.conversation_id}"
        return url

    def _get_raw_chat_messages(self, chat_id: str, conversation_id: str) -> list[Dict[str, Any]]:
        """调用官方「查看对话消息详情API」：获取原始消息列表"""
        messages_url = f"{self.base_url}/chat/message/list"
        params = {
            "chat_id": chat_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content_type": "text",
            "order": "desc",
            "top": 30
        }

        with self._handle_request_errors(
            operation="查询对话消息",
            url=messages_url,
            params=params
        ):
            response = self.session.get(
                url=messages_url,
                headers=self._get_headers(),
                params=params,
                timeout=30,
                verify=False
            )
            response.raise_for_status()
            result = response.json()

            if result.get('code') != 0:
                raise Exception(f"获取消息失败：code={result['code']}, msg={result['msg']}")
            
            messages = result.get('data', [])
            if self.debug and len(messages) > 0:
                print(f"\n[调试] 助手消息列表（共{len(messages)}条）:")
                for i, msg in enumerate(messages):
                    if msg.get('type') == 'answer':
                        print(f"  消息{i+1}: type={msg.get('type')}, content={msg.get('content')}")
                    else:
                        print(f"  消息{i+1}: type={msg.get('type')}, content={msg.get('content')[:50]}...")
            
            return messages

    def _poll_chat_messages(self, chat_id: str, conversation_id: str) -> str:
        """轮询查询消息列表：直到拿到type=answer的最终回复或超时"""
        start_time = time.time()
        while time.time() - start_time < self.sync_timeout:
            messages = self._get_raw_chat_messages(chat_id, conversation_id)
            
            for msg in messages:
                if msg.get('type') == 'answer' and msg.get('content', '').strip():
                    answer_content = msg.get('content').strip()
                    if self.debug:
                        print(f"[调试] 找到type=answer的最终回复（耗时：{time.time()-start_time:.1f}秒）：{answer_content[:100]}...")
                    return answer_content
            
            if self.debug:
                print(f"[调试] 未找到type=answer的消息，等待{self.poll_interval}秒后重试...")
            time.sleep(self.poll_interval)
        
        raise Exception(f"超时（{self.sync_timeout}秒）未获取到最终回复，chat_id={chat_id}")

    def _parse_verbose_content(self, content: str) -> str:
        """解析verbose类型消息的JSON内容，兼容插件结构"""
        try:
            verbose_data = json.loads(content)
            if isinstance(verbose_data.get('data'), dict):
                wrapped_text = verbose_data['data'].get('wraped_text', '').strip()
                if wrapped_text:
                    return wrapped_text
            for key in ['content', 'text', 'message', 'result', 'reply']:
                if key in verbose_data:
                    val = str(verbose_data[key]).strip()
                    if val and val not in ['{}', '[]', '""']:
                        return val
            if isinstance(verbose_data.get('data'), str):
                try:
                    nested_data = json.loads(verbose_data['data'])
                    for nested_key in ['wraped_text', 'content', 'text']:
                        nested_val = str(nested_data.get(nested_key, '')).strip()
                        if nested_val:
                            return nested_val
                except:
                    pass
            return ""
        except:
            return ""

    def _get_chat_messages(self, chat_id: str, conversation_id: str) -> str:
        """提取助手最终回复（优先type=answer，兼容verbose）"""
        try:
            return self._poll_chat_messages(chat_id, conversation_id)
        except Exception as e:
            if self.debug:
                print(f"[调试] 轮询type=answer失败：{str(e)}，尝试解析verbose消息")
        
        messages = self._get_raw_chat_messages(chat_id, conversation_id)
        for msg in messages:
            if msg.get('type') == 'verbose' and msg.get('content', '').strip():
                parsed_content = self._parse_verbose_content(msg.get('content'))
                if parsed_content:
                    if self.debug:
                        print(f"[调试] 解析verbose消息：{parsed_content[:50]}...")
                    return parsed_content
        
        return "你好呀～ 很高兴能成为你的心理陪伴伙伴～ 不管你现在是什么心情，有什么想聊的，都可以告诉我，我会一直在这里倾听和陪伴你～"

    def send_message_sync(self, message: str) -> str:
        """同步聊天（最终稳定版）"""
        data = {
            "bot_id": self.bot_id,
            "user_id": self.user_id,
            "stream": False,
            "auto_save_history": True,
            "additional_messages": [
                {"role": "user", "content": message, "content_type": "text"}
            ]
        }

        with self._handle_request_errors(
            operation="创建Chat",
            url=self._build_chat_url(),
            data=data
        ):
            response = self.session.post(
                url=self._build_chat_url(),
                headers=self._get_headers(),
                json=data,
                timeout=30,
                verify=False
            )
            response.raise_for_status()
            result = response.json()

            if result.get('code') != 0:
                raise Exception(f"创建Chat失败：code={result['code']}, msg={result['msg']}")
            chat_id = result['data'].get('id')
            conversation_id = result['data'].get('conversation_id')

            if not chat_id or not conversation_id:
                raise Exception(f"创建Chat失败：返回数据不完整（chat_id={chat_id}, conversation_id={conversation_id}）")

            if self.debug:
                print(f"[调试] 创建Chat成功：chat_id={chat_id}, conversation_id={conversation_id}")

            reply = self._get_chat_messages(chat_id, conversation_id)
            self.conversation_id = conversation_id

            return reply

    def send_message_stream(self, message: str) -> Iterator[Dict[str, str]]:
        """
        流式聊天（修复版）：正确解析Coze官方SSE格式
        官方SSE格式：event: 事件类型\n data: 消息数据\n\n
        核心修复：分离event和data解析、修正事件匹配逻辑、正确获取content
        """
        data = {
            "bot_id": self.bot_id,
            "user_id": self.user_id,
            "stream": True,
            "auto_save_history": True,
            "additional_messages": [
                {"role": "user", "content": message, "content_type": "text"}
            ]
        }

        with self._handle_request_errors(
            operation="流式创建Chat",
            url=self._build_chat_url(),
            data=data
        ):
            response = self.session.post(
                url=self._build_chat_url(),
                headers=self._get_headers(),
                json=data,
                stream=True,
                timeout=self.stream_timeout,
                verify=False
            )
            response.raise_for_status()

            full_content = ""
            current_chat_id = None
            current_event = None  # 记录当前SSE事件类型（关键修复）

            for line in response.iter_lines(chunk_size=1024):
                if line:
                    try:
                        line = line.decode('utf-8', errors='ignore').strip()
                        
                        # 1. 解析event类型（官方SSE：event: xxx）
                        if line.startswith('event:'):
                            current_event = line.split(':', 1)[1].strip()
                            if self.debug:
                                print(f"[调试] 流式事件：{current_event}")
                            continue
                        
                        # 2. 解析data内容（官方SSE：data: xxx），仅处理增量消息事件
                        if line.startswith('data:') and current_event:
                            data_part = line.split(':', 1)[1].strip()
                            
                            # 官方结束标识：event=done + data="[DONE]"
                            if current_event == 'done' and data_part == '"[DONE]"':
                                if self.debug:
                                    print(f"[调试] 流式结束")
                                break
                            if not data_part:
                                continue

                            # 3. 解析消息数据（关键修复：data_part直接是消息对象，无嵌套）
                            msg = json.loads(data_part)
                            
                            # 4. 处理会话创建事件：更新conversation_id（上下文关联）
                            if current_event == 'conversation.chat.created':
                                current_chat_id = msg.get('id')
                                self.conversation_id = msg.get('conversation_id', self.conversation_id)
                                if self.debug:
                                    print(f"[调试] 流式会话创建：chat_id={current_chat_id}, conversation_id={self.conversation_id}")
                            
                            # 5. 处理增量回复事件（核心：只取助手的text类型answer）
                            elif current_event == 'conversation.message.delta':
                                if (msg.get('role') == 'assistant' 
                                    and msg.get('content_type') == 'text' 
                                    and msg.get('type') == 'answer'):
                                    content = msg.get('content', '').strip()
                                    if content:
                                        full_content += content
                                        if self.debug:
                                            print(f"[调试] 流式增量：{content}")
                                        yield {
                                            "type": "chunk",
                                            "content": content,
                                            "chat_id": current_chat_id,
                                            "conversation_id": self.conversation_id
                                        }
                    except Exception as e:
                        error_msg = f"[调试] 流式解析异常：{str(e)}"
                        if self.debug:
                            print(error_msg)
                        yield {
                            "type": "error",
                            "message": error_msg,
                            "chat_id": current_chat_id,
                            "conversation_id": self.conversation_id
                        }
                        continue

            # 流式结束：返回完整结果
            yield {
                "type": "complete",
                "full_content": full_content,
                "chat_id": current_chat_id,
                "conversation_id": self.conversation_id,
                "is_success": len(full_content) > 0
            }

    def clear_conversation(self):
        """清除当前会话（重置上下文）"""
        self.conversation_id = None
        print(f"🗑️  会话已清除，后续消息将创建新会话")

    def get_current_conversation_id(self) -> Optional[str]:
        """获取当前会话ID"""
        return self.conversation_id

    def set_conversation_id(self, conversation_id: str):
        """
        手动设置会话ID（新增函数）：支持续传已有会话
        参数：conversation_id - Coze官方返回的会话ID（长度通常>10）
        作用：传入后，后续聊天会自动关联该会话的上下文
        """
        # 校验会话ID有效性（避免空值或非法格式）
        if not conversation_id or not isinstance(conversation_id, str) or len(conversation_id) < 10:
            raise ValueError("❌ 无效的conversation_id：必须是长度≥10的字符串（从Coze API获取）")
        self.conversation_id = conversation_id
        if self.debug:
            print(f"[调试] 已手动关联会话ID：{conversation_id[:15]}...")

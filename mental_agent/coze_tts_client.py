#!/usr/bin/env python3
"""
Coze 文本转语音独立客户端（严格匹配官方 API 文档）
核心功能：将文本转为 MP3 音频文件（同步返回）
接口规范参考：https://www.coze.cn/open/docs/developer_guides/text_to_speech
基础信息：
- 请求方式：POST
- 请求地址：https://api.coze.cn/v1/audio/speech
- 权限要求：createSpeech（需在 Coze 平台开通该权限）
参数说明（官方标准）：
- input：必填，合成语音的文本（UTF-8 编码，长度≤1024 字节）
- voice_id：必填，音频音色 ID（需通过「查看音色列表 API」获取可用值）
- emotion：可选，情感类型（仅多情感音色支持，枚举值：happy/sad/angry/surprised/fear/hate/excited/coldness/neutral）
- emotion_scale：可选，情感强度（1.0~5.0，数值越高情感越强烈，默认值：4.0）
"""

import os
import json
import traceback
import requests
import ssl
from dotenv import load_dotenv
from typing import Optional, Dict, Iterator, Literal
from contextlib import contextmanager
from urllib3.poolmanager import PoolManager
from urllib3.exceptions import InsecureRequestWarning

# 禁用不安全请求警告（开发环境）
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 加载环境变量（需配置 COZE_API_TOKEN）
load_dotenv()

# 定义情感类型枚举（严格按官方文档）
EmotionType = Literal["happy", "sad", "angry", "surprised", "fear", "hate", "excited", "coldness", "neutral"]
TEST_VOICE_ID = "7426725529681657907"  # 多情感音色 ID（需通过查看音色列表 API 获取）

# ==================== 自定义 SSL 适配器（兼容 Python 3.7+）====================
class TLSAdapter(requests.adapters.HTTPAdapter):
    def __init__(self):
        super().__init__()

    def init_poolmanager(self, connections, maxsize, block=False):
        """修复 SSL 上下文参数错误，强制 TLSv1.2+（确保和 Coze API 兼容）"""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False  # 开发环境禁用主机名验证
        context.verify_mode = ssl.CERT_NONE  # 开发环境禁用证书验证
        
        # 强制最小 TLS 版本为 1.2（Coze API 要求）
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

# ==================== 文本转语音核心客户端（匹配官方 API）====================
class CozeTTSClient:
    def __init__(self, debug: bool = False):
        # 核心配置（严格按官方文档）
        self.api_token = os.getenv('COZE_API_TOKEN')
        self.tts_url = "https://api.coze.cn/v1/audio/speech"  # 官方正确请求地址
        self.debug = debug  # 调试模式
        self.timeout = 30  # 请求超时时间（秒）

        # 校验必填配置
        if not self.api_token:
            raise ValueError("❌ 请设置 COZE_API_TOKEN 环境变量（从 Coze 开放平台获取，需开通 createSpeech 权限）")

        # 初始化 requests 会话（适配 TLSv1.2+，复用聊天功能的网络配置）
        self.session = requests.Session()
        self.session.mount("https://", TLSAdapter())

    def _get_headers(self) -> Dict[str, str]:
        """获取官方规范的请求头（Authorization + Content-Type）"""
        return {
            "Authorization": f"Bearer {self.api_token}",  # 官方要求的鉴权格式
            "Content-Type": "application/json",  # 官方要求的请求体格式
            "User-Agent": "Coze-Python-TTS-Client/1.0"
        }

    @contextmanager
    def _handle_request_errors(self, operation: str, url: str = "", data: dict = None):
        """统一错误处理：打印请求详情+异常堆栈（方便排查权限/参数问题）"""
        try:
            yield
        except requests.exceptions.RequestException as e:
            error_msg = f"\n❌ {operation}失败！"
            error_msg += f"\n请求URL: {url}"
            error_msg += f"\n请求头: {json.dumps(self._get_headers(), ensure_ascii=False)}"
            if data:
                error_msg += f"\n请求体: {json.dumps(data, ensure_ascii=False)}"
            error_msg += f"\n错误类型: {type(e).__name__}"
            error_msg += f"\n错误描述: {str(e)}"
            
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\n响应状态码: {e.response.status_code}"
                try:
                    resp_json = e.response.json()
                    error_msg += f"\nAPI响应（官方错误信息）: {json.dumps(resp_json, ensure_ascii=False, indent=2)}"
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

    def text_to_speech(
        self,
        input: str,  # 字段名按官方要求：input（而非input_text）
        voice_id: str,
        emotion: Optional[EmotionType] = None,
        emotion_scale: Optional[float] = None
    ) -> Iterator[bytes]:
        """
        文本转语音核心方法（同步流式返回音频，匹配官方 API）
        :param input: 待转换文本（必填，UTF-8 编码，≤1024 字节）
        :param voice_id: 音色 ID（必填，需通过「查看音色列表 API」获取可用值，开通 createSpeech 权限）
        :param emotion: 情感类型（可选，仅多情感音色支持，枚举值见类注释）
        :param emotion_scale: 情感强度（可选，1.0~5.0，默认4.0，数值越高情感越强烈）
        :return: 音频字节流迭代器（MP3格式，官方默认输出格式）
        """
        # 1. 校验必填参数：input（文本）
        if not input or not isinstance(input, str) or len(input.strip()) == 0:
            raise ValueError("❌ 输入文本不能为空（必填参数）")
        input_text = input.strip()
        # 校验 UTF-8 字节长度（≤1024 字节，官方硬性限制）
        input_bytes = input_text.encode('utf-8')
        if len(input_bytes) > 1024:
            raise ValueError(f"❌ 输入文本 UTF-8 编码后长度为 {len(input_bytes)} 字节，超过最大限制 1024 字节")
        
        # 2. 校验必填参数：voice_id（音色ID）
        if not voice_id or not isinstance(voice_id, str) or len(voice_id.strip()) == 0:
            raise ValueError("❌ 音色 ID（voice_id）为必填参数，请通过「查看音色列表 API」获取可用值")
        voice_id = voice_id.strip()
        
        # 3. 构造官方要求的请求体
        request_data = {
            "input": input_text,  # 字段名严格匹配官方：input
            "voice_id": voice_id,
        }
        
        # 4. 校验可选参数：emotion（严格匹配官方枚举值）
        if emotion is not None:
            emotion = emotion.strip().lower()
            valid_emotions: list[EmotionType] = ["happy", "sad", "angry", "surprised", "fear", "hate", "excited", "coldness", "neutral"]
            if emotion not in valid_emotions:
                raise ValueError(f"❌ 无效的情感类型：{emotion}，支持的枚举值：{', '.join(valid_emotions)}")
            request_data["emotion"] = emotion
        
        # 5. 校验可选参数：emotion_scale（官方范围 1.0~5.0，默认4.0）
        if emotion_scale is None:
            request_data["emotion_scale"] = 4.0  # 官方默认值
        else:
            if not isinstance(emotion_scale, (int, float)):
                raise ValueError("❌ 情感强度必须是数字（1.0~5.0）")
            emotion_scale = float(emotion_scale)
            if emotion_scale < 1.0 or emotion_scale > 5.0:
                raise ValueError("❌ 情感强度需在 1.0~5.0 之间（数值越高情感越强烈，官方限制）")
            request_data["emotion_scale"] = emotion_scale
        
        # 调试日志（打印官方要求的完整请求信息）
        if self.debug:
            print(f"[调试] 发起官方 TTS API 请求：")
            print(f"  URL: {self.tts_url}")
            print(f"  Headers: {json.dumps(self._get_headers(), ensure_ascii=False)}")
            print(f"  Body: {json.dumps(request_data, ensure_ascii=False)}")
        
        # 6. 调用 Coze 官方 TTS API（流式获取音频，避免内存占用）
        with self._handle_request_errors(
            operation="文本转语音（官方API）",
            url=self.tts_url,
            data=request_data
        ):
            response = self.session.post(
                url=self.tts_url,
                headers=self._get_headers(),
                json=request_data,
                stream=True,
                timeout=self.timeout,
                verify=False
            )
            response.raise_for_status()  # 抛出 HTTP 错误（4xx/5xx，如权限不足、参数错误等）
            
            # 7. 流式返回音频字节（官方返回的是 MP3 二进制流）
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
            
            if self.debug:
                content_length = response.headers.get('Content-Length', '未知')
                content_type = response.headers.get('Content-Type', '未知')
                print(f"[调试] TTS 音频流返回完成：")
                print(f"  音频格式：{content_type}（官方默认 MP3）")
                print(f"  音频大小：{content_length} 字节")

    def save_to_file(
        self,
        input: str,
        voice_id: str,
        output_path: str = "output.mp3",
        emotion: Optional[EmotionType] = None,
        emotion_scale: Optional[float] = None
    ):
        """
        文本转语音并保存为本地 MP3 文件（直接调用官方 API）
        :param input: 待转换文本（必填）
        :param voice_id: 音色 ID（必填，需开通 createSpeech 权限）
        :param output_path: 输出文件路径（默认 output.mp3）
        :param emotion: 情感类型（可选）
        :param emotion_scale: 情感强度（可选）
        """
        try:
            print(f"📥 正在调用 Coze 官方 TTS API，生成音频文件：{output_path}")
            with open(output_path, 'wb') as f:
                for chunk in self.text_to_speech(input, voice_id, emotion, emotion_scale):
                    f.write(chunk)
            print(f"✅ 音频文件保存成功！路径：{os.path.abspath(output_path)}")
        except Exception as e:
            print(f"❌ 保存文件失败：{str(e)}")

# ==================== 测试代码（按官方 API 优化，可直接运行）====================
def main():
    """测试文本转语音功能（匹配官方 API 要求）"""
    try:
        # 初始化客户端（开启调试模式，查看请求详情）
        tts_client = CozeTTSClient(debug=True)
        
        # 注意：替换为以下内容（关键！）
        # 1. 有效的 voice_id：通过「查看音色列表 API」获取（需开通 createSpeech 权限）
        # 2. 确保 COZE_API_TOKEN 已开通 createSpeech 权限（在 Coze 平台令牌管理中检查）
        TEST_VOICE_ID = "7426725529681657907"  # 替换为你的有效音色 ID
        
        # 测试1：基础文本转语音（默认情感强度 4.0，官方默认配置）
        print("="*70)
        print("测试1：基础文本转语音（保存为 basic_output.mp3）")
        print("="*70)
        basic_text = "今天天气怎么样"  # 测试文本（UTF-8 字节数：15，符合≤1024 限制）
        tts_client.save_to_file(
            input=basic_text,
            voice_id=TEST_VOICE_ID,
            output_path="basic_output.mp3"
        )
        
        # 测试2：带情感的文本转语音（开心情绪，强度 5.0，官方最大值）
        print("\n" + "="*70)
        print("测试2：带情感的文本转语音（开心+强度5.0，保存为 happy_output.mp3）")
        print("="*70)
        happy_text = "太棒啦！你今天完成了所有学习目标，真的太优秀了～"
        tts_client.save_to_file(
            input=happy_text,
            voice_id=TEST_VOICE_ID,
            emotion="happy",
            emotion_scale=5.0,
            output_path="happy_output.mp3"
        )
        
        # 测试3：中性情感文本转语音（强度 2.0，低强度）
        print("\n" + "="*70)
        print("测试3：中性情感文本转语音（保存为 neutral_output.mp3）")
        print("="*70)
        neutral_text = "心理健康对每个人都至关重要，学会调节情绪才能更好面对生活。"
        # 打印字节数（验证符合官方限制）
        print(f"[测试] 文本 UTF-8 字节数：{len(neutral_text.encode('utf-8'))}（≤1024 字节）")
        tts_client.save_to_file(
            input=neutral_text,
            voice_id=TEST_VOICE_ID,
            emotion="neutral",
            emotion_scale=2.0,
            output_path="neutral_output.mp3"
        )
        
        print("\n🎉 所有测试完成！请查看生成的 MP3 文件验证效果～")
        print(f"💡 关键提示：")
        print(f"  1. 若提示「权限不足」：请在 Coze 平台为你的 API Token 开通 createSpeech 权限")
        print(f"  2. 若提示「音色 ID 无效」：请通过「查看音色列表 API」获取有效 voice_id 后替换")
        print(f"  3. 若仍有网络问题：该 API 和你的聊天功能同源（api.coze.cn），聊天能通则此 API 也能通")
    
    except Exception as e:
        print(f"\n❌ 测试失败：{str(e)}")

if __name__ == "__main__":
    main()
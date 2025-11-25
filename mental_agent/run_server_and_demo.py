#!/usr/bin/env python3
"""
Coze API 服务启动+接口示例脚本
用途：
1. 开发者快速启动服务并测试功能；
2. 给项目对接同学（前端/后端）提供清晰的接口调用示例；
3. 验证服务端所有核心接口可用性。
新增：文本转语音接口调用示例
新增：情绪分析接口调用示例
"""
import os
import sys
import time
import json
import requests
import subprocess
import socket
from typing import Optional, Dict
from dataclasses import dataclass
from colorama import init, Fore, Style  # 彩色输出（需安装：pip install colorama）

# 初始化彩色输出
init(autoreset=True)

# ==================== 配置项（对接同学可按需修改）====================
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6001
API_BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
# 测试用户信息（模拟真实用户）
TEST_USER_ID = "user_demo_10086"
# 测试TTS配置（对接同学需替换为有效参数）
TEST_VOICE_ID = "7426725529681657907"  # 替换为Coze有效音色ID
# 等待服务启动的最大时间（秒）
MAX_WAIT_SECONDS = 30  # 延长至30秒
# 接口调用超时时间（秒）
API_TIMEOUT = 60  # 延长至60秒
# 健康检查轮询间隔（秒）
HEALTH_CHECK_INTERVAL = 2

# ==================== 工具类/函数 ====================
@dataclass
class ApiResponse:
    """统一封装API响应，方便处理"""
    success: bool
    data: Optional[Dict] = None
    error_msg: Optional[str] = None
    status_code: Optional[int] = None

def print_title(title: str):
    """打印标题（彩色分隔线）"""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.GREEN}[📌 示例] {title}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

def print_code_block(code: str, language: str = "python"):
    """打印代码块（灰色背景，方便复制）"""
    print(f"\n{Fore.LIGHTBLACK_EX}```-{language}")
    print(code.strip())
    print(f"```")

def send_request(method: str, url: str, json_data: Optional[Dict] = None) -> ApiResponse:
    """发送HTTP请求，统一处理响应（修复NoneType异常）"""
    try:
        response = requests.request(
            method=method,
            url=url,
            json=json_data,
            timeout=API_TIMEOUT  # 使用延长后的超时时间
        )
        response.raise_for_status()  # 抛出HTTP错误（4xx/5xx）
        return ApiResponse(
            success=True,
            data=response.json(),
            status_code=response.status_code
        )
    except requests.exceptions.RequestException as e:
        error_msg = f"请求异常：{str(e)}"
        status_code = None
        # 修复核心：先判断e.response是否存在且不为None
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            try:
                error_msg += f" | 响应内容: {e.response.json()}"
            except:
                error_msg += f" | 响应内容: {e.response.text[:200]}"
        return ApiResponse(
            success=False,
            error_msg=error_msg,
            status_code=status_code
        )

def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用（Windows/Linux通用）"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((DEFAULT_HOST, port)) == 0

def kill_process_using_port(port: int):
    """Windows环境下杀死占用端口的进程（辅助功能）"""
    if os.name != "nt":
        print(f"{Fore.YELLOW}[ℹ️  仅Windows支持自动杀进程，Linux/Mac请手动释放端口]{Style.RESET_ALL}")
        return False
    try:
        # 查找占用端口的进程PID
        cmd = f"netstat -ano | findstr :{port}"
        result = subprocess.check_output(cmd, shell=True).decode('gbk')
        if not result:
            return False
        # 提取PID（最后一列）
        pid = result.strip().split()[-1]
        if pid == "0":
            return False
        # 杀死进程
        subprocess.check_call(f"taskkill /F /PID {pid}", shell=True)
        print(f"{Fore.GREEN}[✅ 已杀死占用端口{port}的进程（PID：{pid}）]{Style.RESET_ALL}")
        time.sleep(2)  # 等待进程释放端口
        return True
    except Exception as e:
        print(f"{Fore.RED}[❌ 自动杀进程失败：{str(e)}]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[ℹ️  请手动执行命令释放端口：]")
        print(f"  1. 查找PID：netstat -ano | findstr :{port}")
        print(f"  2. 杀死进程：taskkill /F /PID 你的PID")
        return False

def start_api_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, debug: bool = False):
    """启动API服务（修复返回值类型不一致问题）"""
    # 步骤1：检查端口是否被占用
    if is_port_in_use(port):
        print(f"{Fore.RED}[❌ 端口{port}已被占用！]{Style.RESET_ALL}")
        choice = input(f"{Fore.YELLOW}[ℹ️  是否自动杀死占用进程？（y/n）]{Style.RESET_ALL} ").strip().lower()
        if choice == "y":
            if not kill_process_using_port(port):
                return (False, None)  # 始终返回元组
        else:
            print(f"{Fore.RED}[❌ 请手动释放端口{port}后重新运行脚本]{Style.RESET_ALL}")
            return (False, None)  # 始终返回元组
    
    print(f"\n{Fore.YELLOW}[ℹ️  正在启动API服务... 地址：{host}:{port}]{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[ℹ️  服务日志将实时输出（按Ctrl+C可终止服务）]{Style.RESET_ALL}")
    
    # 检查是否已安装依赖
    required_packages = ["fastapi", "uvicorn", "requests", "colorama"]
    missing_packages = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)
    if missing_packages:
        print(f"{Fore.RED}[❌ 缺少依赖包：{', '.join(missing_packages)}]")
        print(f"{Fore.GREEN}[ℹ️  正在自动安装...]{Style.RESET_ALL}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
    
    # 启动命令（关键：不隐藏stdout/stderr，显示服务日志）
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api_server:app",
        "--host", host,
        "--port", str(port),
        "--log-level", "info"  # 显示info级别日志，方便排查
    ]
    if debug:
        cmd.append("--reload")  # 调试模式：代码修改自动重启
    
    # 启动子进程（Windows用CREATE_NEW_PROCESS_GROUP，避免Ctrl+C传递）
    proc = None
    try:
        if os.name == "nt":
            proc = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            proc = subprocess.Popen(cmd)
    except Exception as e:
        print(f"{Fore.RED}[❌ 启动服务失败：{str(e)}]{Style.RESET_ALL}")
        return (False, None)  # 始终返回元组
    
    # 步骤2：等待服务就绪（延长时间+多次轮询）
    print(f"\n{Fore.YELLOW}[ℹ️  等待服务启动...（最多等待{MAX_WAIT_SECONDS}秒，每{HEALTH_CHECK_INTERVAL}秒检查一次）]{Style.RESET_ALL}")
    for _ in range(MAX_WAIT_SECONDS // HEALTH_CHECK_INTERVAL):
        time.sleep(HEALTH_CHECK_INTERVAL)
        # 健康检查：调用/health接口
        health_response = send_request("GET", f"{API_BASE_URL}/health")
        if health_response.success:
            print(f"{Fore.GREEN}[✅ API服务启动成功！访问 {API_BASE_URL}/docs 查看接口文档]{Style.RESET_ALL}")
            return (True, proc)  # 始终返回元组
        else:
            print(f"{Fore.YELLOW}[ℹ️  服务尚未就绪：{health_response.error_msg[:50]}...]{Style.RESET_ALL}")
    
    # 服务启动超时
    print(f"{Fore.RED}[❌ 服务启动超时！]{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[ℹ️  排查步骤：]")
    print(f"  1. 查看上方服务日志，是否有报错（如Coze密钥错误、依赖缺失）；")
    print(f"  2. 确认网络正常，能访问Coze API；")
    print(f"  3. 尝试使用--debug模式启动，查看更多日志。")
    if proc:
        proc.terminate()  # 终止未就绪的服务进程
    return (False, None)  # 始终返回元组

# ==================== 核心接口调用示例 ====================
def demo_sync_chat():
    """示例1：同步聊天（阻塞等待完整回复）"""
    print_title("同步聊天（适合简单问答场景）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/chat"
    request_data = {
        "user_id": TEST_USER_ID,
        "message": "I met a handsome boy just now.",
        # 可选：传入session_id（已有会话）或conversation_id（续传Coze会话）
        # "session_id": "xxx",
        # "conversation_id": "xxx"
    }
    
    # 2. 打印调用示例（给对接同学复制用）
    code_example = f"""
import requests

API_BASE_URL = "{API_BASE_URL}"
request_data = {json.dumps(request_data, ensure_ascii=False, indent=2)}

# 延长超时时间至60秒，避免网络/Coze接口延迟导致超时
response = requests.post(
    f"{API_BASE_URL}/chat",
    json=request_data,
    timeout=60
)
print("响应结果：", response.json())
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用并打印结果
    print(f"\n{Fore.BLUE}[🚀 发起同步聊天请求...（超时时间：{API_TIMEOUT}秒）]{Style.RESET_ALL}")
    response = send_request("POST", api_url, request_data)
    
    if response.success:
        print(f"{Fore.GREEN}[✅ 响应成功]{Style.RESET_ALL}")
        print(f"  会话ID（session_id）：{Fore.YELLOW}{response.data['session_id']}")
        print(f"  Coze会话ID（conversation_id）：{Fore.YELLOW}{response.data['conversation_id']}")
        print(f"  助手回复：{response.data['response']}")
        # 保存会话ID，供后续示例使用
        return response.data["session_id"], response.data["conversation_id"], response.data["response"]  # 新增返回回复文本
    else:
        print(f"{Fore.RED}[❌ 响应失败：{response.error_msg}]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[ℹ️  排查步骤：]")
        print(f"  1. 检查api_server.py中Coze API配置是否正确（如密钥、endpoint）；")
        print(f"  2. 确认网络能访问Coze API；")
        print(f"  3. 尝试延长API_TIMEOUT时间（在脚本顶部配置项）。")
        return None, None, None  # 新增返回值

def demo_stream_chat(session_id: str, conversation_id: str):
    """示例2：流式聊天（实时返回回复片段，适合长文本场景）"""
    print_title("流式聊天（适合长回复/实时交互场景）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/chat/stream"
    request_data = {
        "user_id": TEST_USER_ID,
        "session_id": session_id,  # 复用同步聊天的session_id，续传上下文
        "conversation_id": conversation_id,  # 复用Coze会话ID
        "message": "I am hurted by a friend."
    }
    
    # 2. 打印调用示例（给对接同学复制用）
    code_example = f"""
import requests
import json

API_BASE_URL = "{API_BASE_URL}"
request_data = {json.dumps(request_data, ensure_ascii=False, indent=2)}

# 流式响应需要逐行读取，延长超时时间
response = requests.post(
    f"{API_BASE_URL}/chat/stream",
    json=request_data,
    stream=True,  # 关键：启用流式响应
    timeout=120  # 流式响应超时时间更长（如120秒）
)

full_content = ""
for line in response.iter_lines():
    if line:
        # 解析SSE格式：data: {json}
        line = line.decode('utf-8').lstrip('data: ').strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data['type'] == 'chunk':
                # 实时打印片段（前端可实时渲染）
                content = data['data']['content']
                print(content, end='', flush=True)
                full_content += content
            elif data['type'] == 'complete':
                print("\\n\\n流式结束，完整内容：", full_content)
            elif data['type'] == 'error':
                print("\\n\\n错误：", data['data']['message'])
        except json.JSONDecodeError:
            print("\\n\\n解析响应失败：", line)
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用并打印结果
    print(f"\n{Fore.BLUE}[🚀 发起流式聊天请求...（超时时间：120秒）]{Style.RESET_ALL}")
    print(f"  用户消息：{request_data['message']}")
    print(f"  助手回复：", end='', flush=True)
    
    try:
        response = requests.post(
            api_url,
            json=request_data,
            stream=True,
            timeout=120  # 流式超时延长至120秒
        )
        full_content = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8').lstrip('data: ').strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data['type'] == 'chunk':
                        content = data['data']['content']
                        print(content, end='', flush=True)
                        full_content += content
                    elif data['type'] == 'complete':
                        print(f"\n{Fore.GREEN}\\n[✅ 流式聊天完成]{Style.RESET_ALL}")
                        print(f"  总片段数：{data['data']['total_chunks']}")
                        print(f"  完整回复：{full_content}")
                    elif data['type'] == 'error':
                        print(f"\n{Fore.RED}[❌ 流式错误：{data['data']['message']}]{Style.RESET_ALL}")
                except json.JSONDecodeError:
                    print(f"\n{Fore.RED}[❌ 解析流式响应失败：{line}]{Style.RESET_ALL}")
        return full_content  # 新增返回完整回复文本
    except Exception as e:
        print(f"\n{Fore.RED}[❌ 流式调用失败：{str(e)}]{Style.RESET_ALL}")
        return None  # 新增返回值

def demo_bind_conversation(session_id: str, new_conversation_id: Optional[str] = None):
    """示例3：绑定会话ID（手动关联session_id和conversation_id）"""
    print_title("绑定会话ID（适合多端共享/续传已有会话场景）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/session/{session_id}/bind"
    # 用新的conversation_id（模拟用户已有Coze会话ID，需要绑定到当前session）
    conversation_id = new_conversation_id or "7572820707295723572"  # 示例ID，实际替换为真实值
    request_data = {
        "conversation_id": conversation_id
    }
    
    # 2. 打印调用示例
    code_example = f"""
import requests

API_BASE_URL = "{API_BASE_URL}"
session_id = "{session_id}"  # 你的应用会话ID
request_data = {json.dumps(request_data, ensure_ascii=False, indent=2)}

response = requests.post(
    f"{API_BASE_URL}/session/{{session_id}}/bind",
    json=request_data,
    timeout=60
)
print("绑定结果：", response.json())
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用
    print(f"\n{Fore.BLUE}[🚀 发起会话绑定请求...]{Style.RESET_ALL}")
    print(f"  绑定目标：session_id={session_id} → conversation_id={conversation_id[:15]}...")
    response = send_request("POST", api_url, request_data)
    
    if response.success:
        print(f"{Fore.GREEN}[✅ 绑定成功]{Style.RESET_ALL}")
        print(f"  响应：{response.data}")
    else:
        print(f"{Fore.RED}[❌ 绑定失败：{response.error_msg}]{Style.RESET_ALL}")

def demo_query_session(session_id: str):
    """示例4：查询会话信息（获取session绑定的conversation_id、用户信息等）"""
    print_title("查询会话信息（适合状态同步/调试场景）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/session/{session_id}/info"
    
    # 2. 打印调用示例
    code_example = f"""
import requests

API_BASE_URL = "{API_BASE_URL}"
session_id = "{session_id}"  # 要查询的会话ID

response = requests.get(
    f"{API_BASE_URL}/session/{{session_id}}/info",
    timeout=60
)
print("会话信息：", response.json())
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用
    print(f"\n{Fore.BLUE}[🚀 发起会话查询请求...]{Style.RESET_ALL}")
    response = send_request("GET", api_url)
    
    if response.success:
        print(f"{Fore.GREEN}[✅ 查询成功]{Style.RESET_ALL}")
        print(f"  会话详情：{json.dumps(response.data, ensure_ascii=False, indent=2)}")
    else:
        print(f"{Fore.RED}[❌ 查询失败：{response.error_msg}]{Style.RESET_ALL}")

def demo_clear_session(session_id: str):
    """示例5：清除会话（重置上下文，适合用户切换话题/退出场景）"""
    print_title("清除会话（适合重置上下文/用户退出场景）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/session/{session_id}/clear"
    
    # 2. 打印调用示例
    code_example = f"""
import requests

API_BASE_URL = "{API_BASE_URL}"
session_id = "{session_id}"  # 要清除的会话ID

response = requests.post(
    f"{API_BASE_URL}/session/{{session_id}}/clear",
    timeout=60
)
print("清除结果：", response.json())
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用
    print(f"\n{Fore.BLUE}[🚀 发起会话清除请求...]{Style.RESET_ALL}")
    response = send_request("POST", api_url)
    
    if response.success:
        print(f"{Fore.GREEN}[✅ 清除成功]{Style.RESET_ALL}")
        print(f"  响应：{response.data}")
        # 验证清除结果
        check_response = send_request("GET", f"{API_BASE_URL}/session/{session_id}/info")
        if not check_response.success and check_response.status_code == 404:
            print(f"{Fore.GREEN}[✅ 验证：会话已不存在，清除生效]{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[❌ 清除失败：{response.error_msg}]{Style.RESET_ALL}")

def demo_invalid_conversation_id():
    """示例6：错误场景 - 传入无效的conversation_id（验证参数校验）"""
    print_title("错误场景：传入无效的conversation_id（对接时需处理此类异常）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/chat"
    request_data = {
        "user_id": TEST_USER_ID,
        "message": "测试无效会话ID",
        "conversation_id": "invalid_123"  # 无效ID（长度不足10）
    }
    
    # 2. 打印调用示例（修复f-string格式错误）
    code_example = f"""
import requests

API_BASE_URL = "{API_BASE_URL}"
request_data = {json.dumps(request_data, ensure_ascii=False, indent=2)}

try:
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json=request_data,
        timeout=60
    )
    response.raise_for_status()
    print("响应结果：", response.json())
except requests.exceptions.HTTPError as e:
    # 处理无效参数异常（400错误）
    error_data = e.response.json() if e.response else {{"error": str(e)}}
    print("错误处理：", error_data)
    # 前端可提示用户："会话ID无效，请重新发起聊天"
except requests.exceptions.RequestException as e:
    # 处理超时、网络等其他异常
    print("请求异常：", str(e))
    # 前端可提示用户："网络异常，请稍后再试"
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用
    print(f"\n{Fore.BLUE}[🚀 发起无效会话ID请求...]{Style.RESET_ALL}")
    response = send_request("POST", api_url, request_data)
    
    if not response.success and response.status_code == 400:
        print(f"{Fore.YELLOW}[⚠️  预期错误：{response.error_msg}]{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✅ 错误处理生效：对接时需捕获400错误，提示用户会话ID无效]{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[❌ 未按预期返回错误，结果：{response.data or response.error_msg}]{Style.RESET_ALL}")

# -------------------- 新增示例7：文本转语音 --------------------
def demo_text_to_speech(tts_text: str):
    """示例7：文本转语音（适合语音回复/音频下载场景）"""
    print_title("文本转语音（适合语音回复/音频下载场景）")
    
    # 1. 接口信息
    api_url = f"{API_BASE_URL}/text-to-speech"
    request_data = {
        "input": tts_text,  # 使用聊天回复作为TTS文本（模拟真实场景）
        "voice_id": TEST_VOICE_ID,
        "emotion": "neutral",  # 中性情感
        "emotion_scale": 3.0  # 中等情感强度
    }
    
    # 提前定义output_path（修复核心：确保变量始终有定义）
    output_path = "tts_demo_output.mp3"
    
    # 2. 打印调用示例（给对接同学复制用）
    code_example = f"""
import requests
import os

API_BASE_URL = "{API_BASE_URL}"
request_data = {json.dumps(request_data, ensure_ascii=False, indent=2)}

# TTS接口返回音频流，需流式保存
response = requests.post(
    f"{API_BASE_URL}/text-to-speech",
    json=request_data,
    stream=True,  # 关键：启用流式响应
    timeout=60
)

# 保存为MP3文件
output_path = "tts_demo_output.mp3"
with open(output_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024):
        if chunk:
            f.write(chunk)

print(f"音频文件保存成功：{os.path.abspath(output_path)}")
# 前端可直接用 <audio src="接口地址" controls> 播放，无需保存
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 3. 实际调用并保存音频
    print(f"\n{Fore.BLUE}[🚀 发起文本转语音请求...（超时时间：60秒）]{Style.RESET_ALL}")
    print(f"  转换文本：{tts_text[:50]}...")
    print(f"  音色ID：{TEST_VOICE_ID}")
    print(f"  情感配置：neutral（中性），强度：3.0")
    
    try:
        response = requests.post(
            api_url,
            json=request_data,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        # 保存音频文件（使用提前定义的output_path）
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        print(f"{Fore.GREEN}[✅ 文本转语音成功！]{Style.RESET_ALL}")
        print(f"  音频文件路径：{os.path.abspath(output_path)}")
        print(f"  任务ID：{response.headers.get('X-Task-Id', '未知')}")
        print(f"  音频大小：{os.path.getsize(output_path)} 字节")
        print(f"  💡 提示：前端可直接用 <audio src='{api_url}' controls> 播放，无需本地保存")
    except Exception as e:
        print(f"{Fore.RED}[❌ TTS调用失败：{str(e)}]{Style.RESET_ALL}")
        # 移除可能的空文件
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"{Fore.YELLOW}[ℹ️  已清理空音频文件]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[ℹ️  排查步骤：]")
        print(f"  1. 确认COZE_API_TOKEN已开通createSpeech权限；")
        print(f"  2. 确认voice_id是有效值（通过Coze音色列表API获取）；")
        print(f"  3. 文本UTF-8编码后≤1024字节，避免超长；")
        print(f"  4. 确认网络能访问Coze TTS API（api.coze.cn）。")

# -------------------- 新增示例8：情绪分析 --------------------
def demo_emotion_analysis():
    """示例8：情绪分析（为文本打上情绪标签）"""
    print_title("情绪分析（为文本打上情绪标签）")
    
    # 1. 测试文本列表
    test_texts = [
        "I am going to the park with my friends long time no meet",
        "I feel so sad and lonely today",
        "This is the best day of my life!",
        "I'm really angry about what happened",
        "I don't know how to feel about this situation"
    ]
    
    # 2. 接口信息
    api_url = f"{API_BASE_URL}/emotion-analysis"
    
    # 3. 打印调用示例（给对接同学复制用）
    code_example = f"""
import requests

API_BASE_URL = "{API_BASE_URL}"

# 情绪分析请求示例
request_data = {{
    "text": "I feel so happy today!",
    "user_id": "{TEST_USER_ID}"  # 可选
}}

response = requests.post(
    f"{API_BASE_URL}/emotion-analysis",
    json=request_data,
    timeout=60
)

result = response.json()
if result['success']:
    print(f"情绪分析成功：")
    print(f"  输入文本：{{result['input_text']}}")
    print(f"  情绪标签：{{result['emotion_analysis']}}")
    print(f"  Token使用量：{{result.get('token_usage', '未知')}}")
else:
    print(f"情绪分析失败：{{result['error']}}")
"""
    print(f"{Fore.BLUE}[📋 对接示例代码（可直接复制）]{Style.RESET_ALL}")
    print_code_block(code_example)
    
    # 4. 实际调用并打印结果
    print(f"\n{Fore.BLUE}[🚀 发起情绪分析请求...（测试{len(test_texts)}个文本样例）]{Style.RESET_ALL}")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{Fore.YELLOW}[📝 测试文本 {i}/{len(test_texts)}]{Style.RESET_ALL}")
        print(f"  文本内容：{text}")
        
        request_data = {
            "text": text,
            "user_id": TEST_USER_ID
        }
        
        response = send_request("POST", api_url, request_data)
        
        if response.success:
            data = response.data
            if data['success']:
                print(f"  {Fore.GREEN}✅ 情绪标签：{data['emotion_analysis']}{Style.RESET_ALL}")
                if data.get('token_usage'):
                    print(f"  📊 Token使用量：{data['token_usage']}")
            else:
                print(f"  {Fore.RED}❌ 分析失败：{data.get('error', '未知错误')}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ 请求失败：{response.error_msg}{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}[✅ 情绪分析示例完成]{Style.RESET_ALL}")
    print(f"  💡 应用场景：")
    print(f"    • 用户消息情感分析")
    print(f"    • 客服对话情绪监控") 
    print(f"    • 心理健康评估辅助")
    print(f"    • 内容审核情感判断")

# ==================== 主流程 ====================
def main():
    # 先声明全局变量
    global DEFAULT_PORT, API_BASE_URL
    
    # 解析命令行参数（支持自定义端口、调试模式）
    import argparse
    parser = argparse.ArgumentParser(description="Coze API 服务启动+接口调用示例")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"服务端口（默认：{DEFAULT_PORT}）")
    parser.add_argument("--debug", action="store_true", help="启用调试模式（代码修改自动重启服务）")
    args = parser.parse_args()
    
    # 更新全局变量（端口/URL）
    DEFAULT_PORT = args.port
    API_BASE_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
    
    # 步骤1：启动服务（修复解包错误，函数始终返回元组）
    print(f"{Fore.GREEN}{'='*80}")
    print(f"Coze API 服务启动+接口示例脚本（Windows优化版，支持文本转语音和情绪分析）")
    print(f"{'='*80}{Style.RESET_ALL}")
    service_started, proc = start_api_server(port=DEFAULT_PORT, debug=args.debug)
    if not service_started:
        sys.exit(1)
    
    # 步骤2：执行接口示例（按业务流程顺序）
    try:
        # 示例1：同步聊天（获取session_id、conversation_id和回复文本）
        session_id, conversation_id, sync_reply = demo_sync_chat()
        if not session_id or not conversation_id:
            print(f"\n{Fore.RED}[❌ 同步聊天失败，后续示例无法执行]{Style.RESET_ALL}")
            proc.terminate()  # 终止服务进程
            sys.exit(1)
        
        # 示例2：流式聊天（获取完整回复文本，用于TTS）
        stream_reply = demo_stream_chat(session_id, conversation_id)
        
        # 示例3：绑定会话ID（模拟多端共享）
        demo_bind_conversation(session_id, conversation_id)
        
        # 示例4：查询会话信息
        demo_query_session(session_id)
        
        # 示例5：文本转语音（使用同步聊天的回复作为TTS文本）
        if sync_reply:
            demo_text_to_speech(sync_reply)
        else:
            print(f"\n{Fore.YELLOW}[ℹ️  同步聊天无回复文本，跳过TTS示例]{Style.RESET_ALL}")
        
        # 示例6：情绪分析（新增功能演示）
        demo_emotion_analysis()
        
        # 示例7：清除会话
        demo_clear_session(session_id)
        
        # 示例8：错误场景 - 无效conversation_id
        demo_invalid_conversation_id()
        
        # 所有示例完成
        print(f"\n{Fore.GREEN}{'='*80}")
        print(f"🎉 所有接口示例执行完成！")
        print(f"📌 关键提示：")
        print(f"  1. 接口文档：{API_BASE_URL}/docs（Swagger UI，含参数详情）")
        print(f"  2. 对接参考：直接复制示例中的代码块到项目中使用")
        print(f"  3. 会话管理：保存每次响应的 session_id 和 conversation_id，用于续传")
        print(f"  4. 文本转语音：支持流式返回MP3，前端可直接播放或下载")
        print(f"  5. 情绪分析：为文本打上情绪标签，支持心理健康等应用场景")
        print(f"  6. 错误处理：捕获400（参数错误）、500（服务错误）、超时（网络问题）")
        print(f"{'='*80}{Style.RESET_ALL}")
        
        # 保持服务运行（按Ctrl+C终止）
        print(f"\n{Fore.YELLOW}[ℹ️  服务正在后台运行，按Ctrl+C终止脚本和服务...]{Style.RESET_ALL}")
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[ℹ️  脚本被手动终止，正在停止服务...]{Style.RESET_ALL}")
        if proc:
            proc.terminate()
    except Exception as e:
        print(f"\n{Fore.RED}[❌ 脚本执行失败：{str(e)}]{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        if proc:
            proc.terminate()
    finally:
        print(f"\n{Fore.GREEN}[✅ 服务已停止]{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
import json
import os
import platform
import subprocess
import tempfile
import uuid
import sys
from datetime import datetime
from typing import Optional

import requests

sys.stdout.reconfigure(encoding="utf-8")

# === ★ 新增：UTF-8 乱码修复函数 ===
def fix_utf8_garbled(s: str) -> str:
    try:
        return s.encode("latin1").decode("utf-8")
    except:
        return s


# === 1️⃣ Coze API 配置 ===
API_KEY = os.getenv("COZE_API_KEY", "pat_DyjwNAuK4thhVGMDE7WusSNFPFYwfiEEwYOs7WbOoZ9QJjNpXoQXPkNERk2Ld2aO")
BOT_ID = "7559087768224432170"
BASE_URL = "https://api.coze.cn/open_api/v2/chat"

# === 🔊 语音合成配置 ===
VOICE_ID = os.getenv("COZE_VOICE_ID", "7468512265151692827")
SPEECH_URL = "https://api.coze.cn/v1/audio/speech"

# === 2️⃣ HTTP 头 ===
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# === 3️⃣ 会话 & 历史 ===
conversation_id = str(uuid.uuid4())   # 本次脚本运行内保持不变
chat_history = []  # 用于传给 Coze 的对话历史（真正让模型有记忆）


# === 4️⃣ 语音播放 ===
def _auto_play_audio(file_path: str) -> bool:
    def try_command(command):
        try:
            subprocess.run(command, check=False)
            return True
        except FileNotFoundError:
            return False

    system = platform.system()
    if system == "Darwin":
        if try_command(["afplay", file_path]) or try_command(["open", file_path]):
            print("🎵 正在自动播放音频...")
            return True
    elif system == "Windows":
        try:
            os.startfile(file_path)
            print("🎵 正在自动播放音频...")
            return True
        except OSError:
            return False
    else:
        if try_command(["xdg-open", file_path]):
            print("🎵 正在自动播放音频...")
            return True

    print("⚠️ 自动播放失败，请手动播放该文件。")
    return False


def synthesize_speech(text: str, output_file: Optional[str] = None) -> None:
    clean_text = text.strip()
    if not clean_text:
        return

    headers_voice = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "input": clean_text,
        "voice_id": VOICE_ID,
        "response_format": "mp3"
    }

    try:
        response = requests.post(SPEECH_URL, headers=headers_voice, json=body, timeout=30)
    except requests.exceptions.RequestException as exc:
        print(f"⚠️ 语音合成网络异常：{exc}")
        return

    if response.status_code != 200:
        print(f"⚠️ 语音合成失败：{response.status_code} - {response.text}")
        return

    temp_path = None

    try:
        target_path = output_file
        if not target_path:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_path = tmp.name
            tmp.close()
            target_path = temp_path

        with open(target_path, "wb") as f:
            f.write(response.content)

        if output_file:
            print(f"🎧 音频已保存：{output_file}")
        else:
            print("🎧 临时音频已生成，正在播放...")

    except OSError as exc:
        print(f"⚠️ 写入音频文件失败：{exc}")
        if temp_path:
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return

    played = _auto_play_audio(target_path)

    if not output_file and temp_path:
        try:
            if played:
                os.remove(temp_path)
            else:
                print(f"ℹ️ 已保留临时音频文件：{temp_path}")
        except OSError as exc:
            print(f"⚠️ 无法删除临时音频文件：{exc}")


# === 5️⃣ 发送对话 ===
def call_agent(user_input, stream=True):
    global chat_history

    chat_history.append({
        "role": "user",
        "content": user_input,
        "content_type": "text",
    })

    base_payload = {
        "conversation_id": conversation_id,
        "bot_id": BOT_ID,
        "user": "Miya",
        "query": user_input,
        "chat_history": chat_history,
    }

    if stream:
        ok, reply_or_error = _stream_agent_response({**base_payload, "stream": True})
        if ok:
            chat_history.append({
                "role": "assistant",
                "content": reply_or_error,
                "content_type": "text",
            })
            return reply_or_error, True

        print("⚠️ 流式输出失败，改用普通模式。\n")
        fallback = _request_agent_response({**base_payload, "stream": False})
        if not str(fallback).startswith("❌"):
            chat_history.append({
                "role": "assistant",
                "content": fallback,
                "content_type": "text",
            })
        return fallback, False

    reply = _request_agent_response({**base_payload, "stream": False})
    if not str(reply).startswith("❌"):
        chat_history.append({
            "role": "assistant",
            "content": reply,
            "content_type": "text",
        })
    return reply, False


def _request_agent_response(payload):
    try:
        response = requests.post(BASE_URL, headers=headers, data=json.dumps(payload), timeout=60)
        if response.status_code != 200:
            return f"❌ Request failed: {response.status_code} - {response.text}"

        res = response.json()
        messages = res.get("messages", [])

        for msg in messages:
            if msg.get("type") == "answer":
                content = msg.get("content", "").strip()
                # === ★ 修复 emoji 乱码 ===
                return fix_utf8_garbled(content)

        return "⚠️ Agent didn’t return a message."

    except Exception as e:
        return f"❌ Unexpected error: {e}"


def _stream_agent_response(payload):
    try:
        response = requests.post(
            BASE_URL,
            headers=headers,
            data=json.dumps(payload),
            stream=True,
            timeout=60,
        )
    except Exception as e:
        return False, f"❌ Network error: {e}"

    if response.status_code != 200:
        return False, f"❌ Request failed: {response.status_code} - {response.text}"

    reply_parts = []
    print("Agent: ", end="", flush=True)

    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue

        line = raw_line.strip()

        if line.startswith("data:"):
            line = line[len("data:") :].strip()

        if line in ("", "[DONE]"):
            continue

        text_piece = _extract_text_from_stream_payload(line)
        if not text_piece:
            continue

        reply_parts.append(text_piece)
        print(text_piece, end="", flush=True)

    print()

    combined = "".join(reply_parts).strip()

    if combined:
        # === ★ 修复 emoji 乱码 ===
        return True, fix_utf8_garbled(combined)

    return False, "⚠️ Agent didn’t send valid answer content."


def _extract_text_from_stream_payload(payload_str: str) -> Optional[str]:
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        return None

    msg_type = payload.get("msg_type")
    if msg_type and msg_type != "answer":
        return None

    message = payload.get("message")
    if not isinstance(message, dict):
        return None

    if message.get("type") != "answer":
        return None

    content = message.get("content")

    if isinstance(content, str):
        return fix_utf8_garbled(content)

    if isinstance(content, list):
        final_text = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text", "").strip()
                if t:
                    final_text.append(t)
        return fix_utf8_garbled("".join(final_text).strip())

    return None


# === 6️⃣ 保存聊天记录到本地文件 ===
def save_chat_log(user_input, agent_reply):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("chat_history.txt", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}]\nYou: {user_input}\nAgent: {agent_reply}\n\n")


# === 7️⃣ 主循环 ===
if __name__ == "__main__":
    print("💬 Coze Health Agent")

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Session ended，Goodbye！")
                break

            if not user_input:
                print("⚠️ Please enter your message before pressing Enter.\n")
                continue

            reply, streamed = call_agent(user_input, stream=True)

            if not streamed:
                print(f"Agent: {reply}\n")
            else:
                print()

            synthesize_speech(reply)
            save_chat_log(user_input, reply)

        except KeyboardInterrupt:
            print("\n👋 Session interrupted by user")
            break
        except Exception as e:
            print(f"❌ Unexpected error in main loop:{e}")

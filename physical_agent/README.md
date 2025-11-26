Coze Chat Voice Agent

A Python-based conversational agent powered by Coze API, featuring:

✔️ Real-time streaming responses
✔️ Text-to-speech (TTS) with automatic playback
✔️ Conversational memory via chat history
✔️ UTF-8 / emoji decoding fixes
✔️ Cross-platform audio support (macOS / Windows / Linux)
✔️ Automatic chat log saving

This script is developed for an academic project but can also serve as a template for personal AI chatbots.

⭐ Features
1. Coze Streaming Chat API

Supports real-time streaming with incremental token printing

Automatically falls back to non-streaming mode

Handles Coze’s SSE-style streaming responses

2. Persistent Chat History

All messages are stored and sent to Coze API so the model maintains context across the conversation.

3. Text-to-Speech (TTS) with Auto Playback

Integrates Coze /v1/audio/speech API to generate MP3 audio:

Creates temporary or user-specified audio files

Automatically plays audio based on OS

Handles errors gracefully and keeps temporary files for manual playback if needed

4. UTF-8 & Emoji Fix

A custom function decodes corrupted emoji such as ðŸ˜…:

s.encode("latin1").decode("utf-8")


This preserves normal text while fixing malformed Unicode.

5. Cross-Platform Audio Player

Audio playback is automatically handled:

OS	Playback Method
macOS	afplay / open
Windows	os.startfile
Linux	xdg-open
6. Chat Log Recording

Each conversation turn is saved into chat_history.txt with timestamps.

📁 Project Structure
project/
│── main.py               # The chat & speech agent script
│── chat_history.txt      # Automatically generated logs
│── README.md             # Project documentation

🔧 Installation & Setup
1. Clone the Repository
git clone https://github.com/yourname/yourrepo.git
cd yourrepo

2. Install Python Dependencies
pip install requests

3. Set Environment Variables
export COZE_API_KEY="your-api-key"
export COZE_VOICE_ID="your-voice-id"   # optional


(You may hardcode them in the script, but this is discouraged.)

4. Run the Agent
python main.py

🗣️ Usage

Once the script starts, simply type your message:

You: I feel stressed today.
Agent: I’m here for you. Would you like to talk about what's causing it?


The system will:

Print streamed responses

Generate an MP3 response

Play the audio automatically

Save the turn in the local log file

To exit:

exit
quit

🧩 Key Components
1. Chat API Payload Structure
{
  "conversation_id": "...",
  "bot_id": "...",
  "query": "...",
  "chat_history": [...]
}

2. TTS Request Structure
{
  "input": "text to speak",
  "voice_id": "your-voice",
  "response_format": "mp3"
}

3. Stream Parsing

Streaming chunks follow the Coze SSE-like structure.
Non-answer messages are filtered out.

4. Audio Playback

Automatically selects the appropriate command depending on OS.


🧪 Tested Environments

macOS 14

Ubuntu 22.04

Python 3.11

Coze API v2 Chat + v1 Audio
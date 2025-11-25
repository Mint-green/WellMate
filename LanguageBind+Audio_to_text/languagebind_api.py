from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import os
import tempfile
from languagebind import LanguageBind, transform_dict, LanguageBindImageTokenizer, to_device
import whisper
import requests
from urllib.parse import urlparse
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np

app = Flask(__name__)
CORS(app)  # 允许跨域请求
app.config['JSON_AS_ASCII'] = False  # 确保中文字符正常显示

# 设置文件上传配置
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 限制上传文件大小为100MB
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

print("正在加载Whisper模型...")
whisper_model = whisper.load_model("base")  # 可以选择 base, small, medium, large
print("Whisper模型加载完成！")

# 初始化LanguageBind模型
print("正在加载LanguageBind模型...")
device = 'cuda' if torch.cuda.is_available() else 'cpu'
device = torch.device(device)

clip_type = {
    'video': 'LanguageBind_Video_FT', 
    'audio': 'LanguageBind_Audio_FT',
    'image': 'LanguageBind_Image'
}

model = LanguageBind(clip_type=clip_type, cache_dir='./cache_dir')
model = model.to(device)
model.eval()

pretrained_ckpt = 'lb203/LanguageBind_Image'
tokenizer = LanguageBindImageTokenizer.from_pretrained(pretrained_ckpt, cache_dir='./cache_dir/tokenizer_cache_dir')
modality_transform = {c: transform_dict[c](model.modality_config[c]) for c in clip_type.keys()}

# 优化后的情绪标签（更准确）
EMOTION_TAGS = [
    "happy", "joyful", "joy", "excited", "satisfied", "pleasure", "comfortable", "refreshing", "smooth",
    "sad", "sadness", "heartbroken", "painful", "depressed", "lost", "hopeless", "melancholy", "sorrow", "grief", "desolation", "depression",
    "angry", "anger",  "furious", "fire energy", "fire intensity", "resentment",
    "anxiety", "nervousness", "unease", "panic", "discomfort",  "restlessness",
    "defeat", "failure",  "frustration",  "discouragement", "disappointment", "setback", "obstruction", "hitting a wall", "helpless",
    "worried", "worry", "troubled", "distressed", "miss", "love",
    "fear", "fearful", "terror", "timidty", "tremble", "shrink back",
    "surprised", "shocking", "suddenly", "unexpected", "caught off guard",
    "disgusted", "nauseous", "nauseating", "unsightly",
    "neutral", "tired", "stressed", "relaxed", "anxious", "confident", "confused"
]

print("模型加载完成！")

SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
SUPPORTED_AUDIO_FORMATS = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma'}
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}

def get_file_extension(filename):
    """安全地获取文件扩展名"""
    if not filename:
        return ''
    return os.path.splitext(filename)[1].lower()

def validate_file_extension(filename, allowed_formats):
    """验证文件扩展名是否在允许的格式中"""
    ext = get_file_extension(filename)
    return ext in allowed_formats

def download_file_from_url(url, timeout=30, modality_type='image'):
    """从URL下载文件到临时文件"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, stream=True, timeout=timeout, headers=headers)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        print(f"下载文件 - URL: {url}, Content-Type: {content_type}, 模态类型: {modality_type}")
        
        # 根据模态类型确定支持的文件格式
        if modality_type == 'image':
            allowed_formats = SUPPORTED_IMAGE_FORMATS
            default_ext = '.jpg'
        elif modality_type == 'audio':
            allowed_formats = SUPPORTED_AUDIO_FORMATS
            default_ext = '.wav'
        elif modality_type == 'video':
            allowed_formats = SUPPORTED_VIDEO_FORMATS
            default_ext = '.mp4'
        else:
            allowed_formats = set()
            default_ext = '.tmp'
        
        # 从URL提取文件扩展名
        parsed_url = urlparse(url)
        file_ext = get_file_extension(parsed_url.path)
        
        # 如果没有扩展名或扩展名不在允许列表中，根据Content-Type猜测
        if not file_ext or file_ext not in allowed_formats:
            if 'jpeg' in content_type or 'jpg' in content_type:
                file_ext = '.jpg'
            elif 'png' in content_type:
                file_ext = '.png'
            elif 'gif' in content_type:
                file_ext = '.gif'
            elif 'webp' in content_type:
                file_ext = '.webp'
            elif 'mp3' in content_type:
                file_ext = '.mp3'
            elif 'wav' in content_type:
                file_ext = '.wav'
            elif 'mp4' in content_type:
                file_ext = '.mp4'
            elif 'avi' in content_type:
                file_ext = '.avi'
            else:
                file_ext = default_ext
        
        print(f"使用文件扩展名: {file_ext}")
        
        # 验证文件格式
        if modality_type != 'unknown' and file_ext not in allowed_formats:
            raise Exception(f"不支持的文件格式: {file_ext}，支持的格式: {', '.join(allowed_formats)}")
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        
        with open(temp_file.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(temp_file.name)
        print(f"下载文件大小: {file_size} bytes")
        
        return temp_file.name
    except Exception as e:
        raise Exception(f"下载文件失败: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "message": "LanguageBind API is running"})

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    语音转文本端点 - 增强版，支持本地路径、URL和文件上传
    接收三种方式：
    1. JSON: {"audio_path": "/path/to/audio.wav"}
    2. JSON: {"audio_url": "https://example.com/audio.wav"}
    3. Form-data: 文件字段名为"audio"
    """
    try:
        temp_files = []  # 用于跟踪临时文件
        
        # 判断请求类型
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 方式3: 文件上传
            if 'audio' not in request.files:
                return jsonify({"success": False, "error": "未提供音频文件"}), 400
            
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({"success": False, "error": "未选择文件"}), 400
            
            # 保存上传的文件到临时位置
            audio_filename = f"{uuid.uuid4()}_{secure_filename(audio_file.filename)}"
            audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
            audio_file.save(audio_path)
            temp_files.append(audio_path)
            
        else:
            # 方式1和2: JSON请求
            data = request.json or {}
            
            if data.get('audio_path'):
                # 方式1: 本地路径
                audio_path = data['audio_path']
                if not os.path.exists(audio_path):
                    return jsonify({"success": False, "error": "音频文件不存在"}), 400
                    
            elif data.get('audio_url'):
                # 方式2: URL下载
                try:
                    audio_path = download_file_from_url(data['audio_url'], modality_type='audio')
                    temp_files.append(audio_path)
                except Exception as e:
                    return jsonify({"success": False, "error": str(e)}), 400
            else:
                return jsonify({"success": False, "error": "请提供audio_path、audio_url或上传音频文件"}), 400
        
        # 使用Whisper进行语音识别
        result = whisper_model.transcribe(audio_path)
        transcribed_text = result["text"].strip()
        
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        return jsonify({
            "success": True,
            "transcribed_text": transcribed_text,
            "language": result.get("language", "未知")
        })
        
    except Exception as e:
        # 确保清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze_multimodal():
    """
    分析多模态数据并计算与情绪标签的相似度 - 增强版
    支持三种输入方式：
    1. 本地路径 (JSON): {"image_path": "/path/to/image.jpg", ...}
    2. URL下载 (JSON): {"image_url": "https://example.com/image.jpg", ...}
    3. 文件上传 (Form-data): 文件字段名为"image", "audio", "video"
    """
    try:
        temp_files = []  # 跟踪所有临时文件
        results = {}
        processed_modalities = []
        
        # 判断请求类型
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 方式3: 文件上传
            data = request.form
            top_k = int(data.get('top_k', 5))
            custom_text = data.get('custom_text')
            
            # 处理上传的图像
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename:
                    image_filename = f"{uuid.uuid4()}_{secure_filename(image_file.filename)}"
                    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
                    image_file.save(image_path)
                    temp_files.append(image_path)
                    
                    image_results = process_image(image_path, top_k, custom_text)
                    results['image'] = image_results
                    processed_modalities.append('image')
            
            # 处理上传的音频
            if 'audio' in request.files:
                audio_file = request.files['audio']
                if audio_file.filename:
                    audio_filename = f"{uuid.uuid4()}_{secure_filename(audio_file.filename)}"
                    audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)
                    audio_file.save(audio_path)
                    temp_files.append(audio_path)
                    
                    audio_results = process_audio(audio_path, top_k, custom_text)
                    results['audio'] = audio_results
                    processed_modalities.append('audio')
            
            # 处理上传的视频
            if 'video' in request.files:
                video_file = request.files['video']
                if video_file.filename:
                    video_filename = f"{uuid.uuid4()}_{secure_filename(video_file.filename)}"
                    video_path = os.path.join(UPLOAD_FOLDER, video_filename)
                    video_file.save(video_path)
                    temp_files.append(video_path)
                    
                    video_results = process_video(video_path, top_k, custom_text)
                    results['video'] = video_results
                    processed_modalities.append('video')
                    
        else:
            # 方式1和2: JSON请求
            data = request.json or {}
            top_k = data.get('top_k', 5)
            custom_text = data.get('custom_text')
            
            # 处理图像 - 支持路径和URL
            image_path = None
            if data.get('image_path'):
                image_path = data['image_path']
                if not os.path.exists(image_path):
                    results['image'] = {"error": "图像文件不存在"}
                else:
                    image_results = process_image(image_path, top_k, custom_text)
                    results['image'] = image_results
                    processed_modalities.append('image')
                    
            elif data.get('image_url'):
                try:
                    image_path = download_file_from_url(data['image_url'], modality_type='image')
                    temp_files.append(image_path)
                    image_results = process_image(image_path, top_k, custom_text)
                    results['image'] = image_results
                    processed_modalities.append('image')
                except Exception as e:
                    results['image'] = {"error": f"图像下载失败: {str(e)}"}
            
            # 处理音频 - 支持路径和URL
            audio_path = None
            if data.get('audio_path'):
                audio_path = data['audio_path']
                if not os.path.exists(audio_path):
                    results['audio'] = {"error": "音频文件不存在"}
                else:
                    audio_results = process_audio(audio_path, top_k, custom_text)
                    results['audio'] = audio_results
                    processed_modalities.append('audio')
                    
            elif data.get('audio_url'):
                try:
                    audio_path = download_file_from_url(data['audio_url'], modality_type='audio')
                    temp_files.append(audio_path)
                    audio_results = process_audio(audio_path, top_k, custom_text)
                    results['audio'] = audio_results
                    processed_modalities.append('audio')
                except Exception as e:
                    results['audio'] = {"error": f"音频下载失败: {str(e)}"}
            
            # 处理视频 - 支持路径和URL
            video_path = None
            if data.get('video_path'):
                video_path = data['video_path']
                if not os.path.exists(video_path):
                    results['video'] = {"error": "视频文件不存在"}
                else:
                    video_results = process_video(video_path, top_k, custom_text)
                    results['video'] = video_results
                    processed_modalities.append('video')
                    
            elif data.get('video_url'):
                try:
                    video_path = download_file_from_url(data['video_url'], modality_type='video')
                    temp_files.append(video_path)
                    video_results = process_video(video_path, top_k, custom_text)
                    results['video'] = video_results
                    processed_modalities.append('video')
                except Exception as e:
                    results['video'] = {"error": f"视频下载失败: {str(e)}"}
        
        # 生成响应
        response = {
            "success": True,
            "processed_modalities": processed_modalities,
            "top_k_used": top_k,
            "custom_text_used": custom_text is not None
        }
        
        if custom_text:
            response["custom_text"] = custom_text
            response["similarity_scores"] = {
                modality: result.get('similarity_score', 0) 
                for modality, result in results.items() 
                if 'similarity_score' in result
            }
        else:
            response["emotion_analysis"] = results
        
        # 清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        return jsonify(response)
        
    except Exception as e:
        # 确保清理临时文件
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def process_image(image_path, top_k=5, custom_text=None):
    """处理图像并计算与情绪标签或自定义文本的相似度"""
    try:
        # 图像格式检查和预处理
        temp_rgb_path = None
        
        # 打开并检查图像
        try:
            pil_image = Image.open(image_path)
            print(f"图像信息 - 模式: {pil_image.mode}, 尺寸: {pil_image.size}, 格式: {pil_image.format}")
            
            # 转换为RGB模式（如果需要）
            if pil_image.mode != 'RGB':
                print(f"转换图像模式: {pil_image.mode} -> RGB")
                pil_image = pil_image.convert('RGB')
                
            # 保存转换后的图像（临时）
            temp_rgb_path = f"/tmp/rgb_converted_{uuid.uuid4()}.jpg"
            pil_image.save(temp_rgb_path, 'JPEG', quality=95)
            image_path = temp_rgb_path  # 使用转换后的图像路径
            
        except Exception as img_error:
            return {"error": f"图像打开失败: {str(img_error)}"}

        if custom_text:
            # 使用自定义文本
            inputs = {
                'image': to_device(modality_transform['image']([image_path]), device),
                'language': to_device(tokenizer([custom_text], max_length=77, padding='max_length', 
                                             truncation=True, return_tensors='pt'), device)
            }
            
            with torch.no_grad():
                embeddings = model(inputs)
            
            # 计算相似度 - 使用余弦相似度而不是softmax
            image_embedding = embeddings['image']
            text_embedding = embeddings['language']
            
            # 归一化向量
            image_embedding = image_embedding / image_embedding.norm(dim=-1, keepdim=True)
            text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            
            # 计算余弦相似度
            similarity = (image_embedding @ text_embedding.T).item()
            
            # 清理临时文件
            if temp_rgb_path and os.path.exists(temp_rgb_path):
                try:
                    os.unlink(temp_rgb_path)
                except:
                    pass
            
            return {"similarity_score": max(0.0, min(1.0, (similarity + 1) / 2))}  # 归一化到0-1
            
        else:
            # 使用情绪标签
            inputs = {
                'image': to_device(modality_transform['image']([image_path]), device),
                'language': to_device(tokenizer(EMOTION_TAGS, max_length=77, padding='max_length', 
                                             truncation=True, return_tensors='pt'), device)
            }
            
            with torch.no_grad():
                embeddings = model(inputs)
            
            # 计算相似度
            similarities = torch.softmax(embeddings['image'] @ embeddings['language'].T, dim=-1)
            similarities = similarities.detach().cpu().numpy()[0]
            
            # 转换为字典格式并排序
            result = {tag: float(score) for tag, score in zip(EMOTION_TAGS, similarities)}
            sorted_result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:top_k])
            
            # 清理临时文件
            if temp_rgb_path and os.path.exists(temp_rgb_path):
                try:
                    os.unlink(temp_rgb_path)
                except:
                    pass
            
            return {
                "top_emotions": sorted_result,
                "primary_emotion": list(sorted_result.keys())[0] if sorted_result else "unknown"
            }

    except Exception as e:
        # 确保清理临时文件
        if 'temp_rgb_path' in locals() and temp_rgb_path and os.path.exists(temp_rgb_path):
            try:
                os.unlink(temp_rgb_path)
            except:
                pass
        return {"error": f"图像处理失败: {str(e)}"}

def process_audio(audio_path, top_k=5, custom_text=None):
    """处理音频并计算与情绪标签或自定义文本的相似度"""
    try:
        if custom_text:
            # 使用自定义文本
            inputs = {
                'audio': to_device(modality_transform['audio']([audio_path]), device),
                'language': to_device(tokenizer([custom_text], max_length=77, padding='max_length',
                                             truncation=True, return_tensors='pt'), device)
            }
            
            with torch.no_grad():
                embeddings = model(inputs)
            
            # 计算相似度
            audio_embedding = embeddings['audio']
            text_embedding = embeddings['language']
            
            audio_embedding = audio_embedding / audio_embedding.norm(dim=-1, keepdim=True)
            text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            
            similarity = (audio_embedding @ text_embedding.T).item()
            
            return {"similarity_score": max(0.0, min(1.0, (similarity + 1) / 2))}
            
        else:
            # 使用情绪标签
            inputs = {
                'audio': to_device(modality_transform['audio']([audio_path]), device),
                'language': to_device(tokenizer(EMOTION_TAGS, max_length=77, padding='max_length',
                                             truncation=True, return_tensors='pt'), device)
            }
            
            with torch.no_grad():
                embeddings = model(inputs)
            
            similarities = torch.softmax(embeddings['audio'] @ embeddings['language'].T, dim=-1)
            similarities = similarities.detach().cpu().numpy()[0]
            
            result = {tag: float(score) for tag, score in zip(EMOTION_TAGS, similarities)}
            sorted_result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:top_k])
            
            return {
                "top_emotions": sorted_result,
                "primary_emotion": list(sorted_result.keys())[0] if sorted_result else "unknown"
            }
        
    except Exception as e:
        return {"error": f"音频处理失败: {str(e)}"}

def process_video(video_path, top_k=5, custom_text=None):
    """处理视频并计算与情绪标签或自定义文本的相似度"""
    try:
        if custom_text:
            # 使用自定义文本
            inputs = {
                'video': to_device(modality_transform['video']([video_path]), device),
                'language': to_device(tokenizer([custom_text], max_length=77, padding='max_length',
                                             truncation=True, return_tensors='pt'), device)
            }
            
            with torch.no_grad():
                embeddings = model(inputs)
            
            # 计算相似度
            video_embedding = embeddings['video']
            text_embedding = embeddings['language']
            
            video_embedding = video_embedding / video_embedding.norm(dim=-1, keepdim=True)
            text_embedding = text_embedding / text_embedding.norm(dim=-1, keepdim=True)
            
            similarity = (video_embedding @ text_embedding.T).item()
            
            return {"similarity_score": max(0.0, min(1.0, (similarity + 1) / 2))}
            
        else:
            # 使用情绪标签
            inputs = {
                'video': to_device(modality_transform['video']([video_path]), device),
                'language': to_device(tokenizer(EMOTION_TAGS, max_length=77, padding='max_length',
                                             truncation=True, return_tensors='pt'), device)
            }
            
            with torch.no_grad():
                embeddings = model(inputs)
            
            similarities = torch.softmax(embeddings['video'] @ embeddings['language'].T, dim=-1)
            similarities = similarities.detach().cpu().numpy()[0]
            
            result = {tag: float(score) for tag, score in zip(EMOTION_TAGS, similarities)}
            sorted_result = dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:top_k])
            
            return {
                "top_emotions": sorted_result,
                "primary_emotion": list(sorted_result.keys())[0] if sorted_result else "unknown"
            }
        
    except Exception as e:
        return {"error": f"视频处理失败: {str(e)}"}

if __name__ == '__main__':
    print("启动LanguageBind API服务...")
    print(f"服务将在 http://0.0.0.0:7860 运行")
    app.run(host='0.0.0.0', port=7860, debug=False)

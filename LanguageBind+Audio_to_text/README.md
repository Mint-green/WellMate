# LanguageBind Multimodal Emotion Recognition & Whisper Audio-to-Text API

## Project Overview

This project implements a multimodal emotion recognition API that combines LanguageBind for multimodal analysis and Whisper for speech-to-text transcription. The system provides real-time emotion analysis from images, audio, and video inputs, along with speech transcription capabilities.

## Features

- **Multimodal Emotion Recognition**: Analyze emotions from images, audio, and video using LanguageBind
- **Speech-to-Text Transcription**: Convert speech to text using OpenAI's Whisper model
- **Multiple Input Methods**: Support for local files, URLs, and direct file uploads
- **Custom Text Analysis**: Calculate similarity between media content and custom text prompts
- **RESTful API**: Fully containerized service with comprehensive API endpoints

## API Endpoints

### Health Check

```bash
GET /health
```

Returns service status and confirms API is running.

### Speech Transcription

```bash
POST /transcribe
```

Supports three input methods:

- Local file path: `{"audio_path": "/path/to/audio.wav"}`
    
- URL download: `{"audio_url": "https://example.com/audio.wav"}`
    
- File upload: Form-data with field name `audio`

### Multimodal Analysis

```bash
POST /analyze
```

Analyzes media content and calculates similarity with emotion labels or custom text. Supports:

- Local file paths
    
- URL downloads
    
- Direct file uploads (form-data)
    
- Custom text similarity analysis

## Technical Architecture

### Core Components

- **LanguageBind**: Multimodal emotion recognition model supporting text, audio, and video
    
- **Whisper**: Speech-to-text transcription model
    
- **Flask**: REST API framework
    
- **Docker**: Containerization for consistent deployment
    

### Model Specifications

- **LanguageBind Models**:
    
    - LanguageBind_Video_FT
        
    - LanguageBind_Audio_FT
        
    - LanguageBind_Image
        
- **Whisper Model**: base version (139M parameters)
    
- **Emotion Labels**: 50+ emotional states including happy, sad, angry, anxious, etc.
    

## Deployment

### Local Development

1. Build the Docker image:
    
```bash
docker build -t languagebind-api .
```

2. Run the container:
    
```bash
docker run -d -p 7860:7860 --gpus all languagebind-api
```

### Cloud Deployment (Aliyun Function Compute)

1. Build and push image to Aliyun Container Registry
    
2. Create function with custom container configuration
    
3. Set environment variables:
    
    - `HF_HUB_OFFLINE=1` (for offline model loading)
        
4. Configure trigger with HTTP protocol
    

## API Usage Examples

### Health Check

```bash
curl -X GET https://your-api-endpoint/health
```

### Speech Transcription

```bash
curl -X POST https://your-api-endpoint/transcribe \
  -F "audio=@/path/to/your/audio.wav"
```

### Image Emotion Analysis

```bash
curl -X POST https://your-api-endpoint/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/workspace/assets/image/0.jpg",
    "top_k": 5
  }'
```

### Custom Text Similarity

```bash
curl -X POST https://your-api-endpoint/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "custom_text": "happy person",
    "top_k": 3
  }'
```

### File Upload with Multiple Modalities

```bash
curl -X POST https://your-api-endpoint/analyze \
  -F "image=@/path/to/image.jpg" \
  -F "audio=@/path/to/audio.wav" \
  -F "top_k=3"
```

## Response Formats

### Health Check Response

```json
{
  "status": "healthy",
  "message": "LanguageBind API is running"
}
```

### Transcription Response

```json
{
  "success": true,
  "transcribed_text": "Recognized speech content",
  "language": "en"
}
```

### Emotion Analysis Response

```json
{
  "success": true,
  "processed_modalities": ["image", "audio"],
  "top_k_used": 3,
  "custom_text_used": false,
  "emotion_analysis": {
    "image": {
      "top_emotions": {
        "happy": 0.85,
        "joyful": 0.76,
        "excited": 0.63
      },
      "primary_emotion": "happy"
    },
    "audio": {
      "top_emotions": {
        "relaxed": 0.72,
        "comfortable": 0.65,
        "smooth": 0.58
      },
      "primary_emotion": "relaxed"
    }
  }
}
```
## Technical Specifications

### System Requirements

- **GPU**: NVIDIA GPU with CUDA 11.6 support
    
- **Memory**: 8GB+ GPU memory recommended
    
- **Storage**: 15GB+ for models and dependencies
    

### Dependencies

- PyTorch 1.13.1 + CUDA 11.6
    
- LanguageBind models
    
- OpenAI Whisper
    
- Flask, Flask-CORS
    
- Transformers, Tokenizers
    
- OpenCV, PyAV
    

### Performance

- **Model Loading**: ~2-3 minutes (cold start)
    
- **Inference Time**: 3-5 seconds per request
    
- **Accuracy**: ~80% on multimodal emotion recognition tasks
    

## Development Notes

### Key Challenges Solved

1. **Model Compatibility**: Resolved dependency conflicts between LanguageBind and Whisper
    
2. **GPU Memory Optimization**: Managed 8GB GPU constraint through selective model loading
    
3. **Cloud Deployment**: Adapted for Aliyun Function Compute with custom container support
    
4. **Network Restrictions**: Implemented offline model loading for cloud environments
    

### Implementation Highlights

- Containerized deployment with Docker
    
- Support for multiple input methods (file paths, URLs, uploads)
    
- Comprehensive error handling and logging
    
- Cross-origin resource sharing (CORS) enabled
    
- Efficient temporary file management
    

## Future Enhancements

- Support for additional modalities (thermal, depth)
    
- Real-time streaming analysis
    
- Batch processing capabilities
    
- Advanced emotion detection with contextual understanding
    
- Multilingual support expansion
    

## License

This project is developed as part of the WellMate holistic health assistance system.
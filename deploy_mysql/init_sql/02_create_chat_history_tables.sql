-- 创建健康对话历史相关表

-- 1. 创建对话会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL UNIQUE DEFAULT (UUID()),
    user_uuid VARCHAR(36) NOT NULL,
    session_type ENUM('physical', 'text', 'general') DEFAULT 'general',
    title VARCHAR(200) DEFAULT NULL,
    conversation_id VARCHAR(36) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 索引
    INDEX idx_user_uuid (user_uuid),
    INDEX idx_session_type (session_type),
    INDEX idx_created_at (created_at),
    INDEX idx_conversation_id (conversation_id)
);

-- 2. 创建对话消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    message_type ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSON DEFAULT NULL,
    
    -- 索引
    INDEX idx_session_id (session_id),
    INDEX idx_message_type (message_type),
    INDEX idx_timestamp (timestamp)
);

-- 3. 创建语音合成记录表
CREATE TABLE IF NOT EXISTS speech_synthesis_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    message_id INT NOT NULL,
    voice_id VARCHAR(50) DEFAULT NULL,
    audio_file_path VARCHAR(500) DEFAULT NULL,
    synthesis_status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME DEFAULT NULL,
    
    -- 索引
    INDEX idx_session_id (session_id),
    INDEX idx_synthesis_status (synthesis_status)
);
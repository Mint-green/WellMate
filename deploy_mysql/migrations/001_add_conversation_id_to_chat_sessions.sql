-- 迁移脚本：为chat_sessions表添加conversation_id字段
-- 执行时间：2024年11月
-- 描述：优化会话管理机制，将conversation_id绑定关系直接存储在chat_sessions表中

-- 检查表是否存在
SET @table_exists = (SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = DATABASE() AND table_name = 'chat_sessions');

-- 如果表存在，检查是否已有conversation_id字段
SET @column_exists = 0;
IF @table_exists > 0 THEN
    SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns 
                         WHERE table_schema = DATABASE() AND table_name = 'chat_sessions' 
                         AND column_name = 'conversation_id');
END IF;

-- 如果表存在且没有conversation_id字段，则添加字段
IF @table_exists > 0 AND @column_exists = 0 THEN
    -- 添加conversation_id字段
    ALTER TABLE chat_sessions 
    ADD COLUMN conversation_id VARCHAR(36) DEFAULT NULL AFTER title;
    
    -- 添加索引
    ALTER TABLE chat_sessions 
    ADD INDEX idx_conversation_id (conversation_id);
    
    -- 从chat_messages表中提取现有的conversation_id并更新到chat_sessions表
    UPDATE chat_sessions cs
    SET cs.conversation_id = (
        SELECT cm.metadata->>'$.conversation_id'
        FROM chat_messages cm
        WHERE cm.session_id = cs.session_id
        AND cm.metadata IS NOT NULL
        AND JSON_EXTRACT(cm.metadata, '$.conversation_id') IS NOT NULL
        ORDER BY cm.created_at DESC
        LIMIT 1
    )
    WHERE EXISTS (
        SELECT 1 FROM chat_messages cm
        WHERE cm.session_id = cs.session_id
        AND cm.metadata IS NOT NULL
        AND JSON_EXTRACT(cm.metadata, '$.conversation_id') IS NOT NULL
    );
    
    SELECT 'Migration completed: conversation_id field added to chat_sessions table' AS result;
ELSEIF @table_exists = 0 THEN
    SELECT 'Table chat_sessions does not exist, skipping migration' AS result;
ELSE
    SELECT 'conversation_id field already exists in chat_sessions table, skipping migration' AS result;
END IF;
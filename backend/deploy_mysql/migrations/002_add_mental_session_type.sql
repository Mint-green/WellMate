-- 添加mental会话类型到chat_sessions表

-- 1. 首先备份现有数据
CREATE TABLE IF NOT EXISTS chat_sessions_backup_002 AS SELECT * FROM chat_sessions;

-- 2. 修改session_type字段的ENUM定义
ALTER TABLE chat_sessions 
MODIFY COLUMN session_type ENUM('physical', 'mental', 'text', 'general') DEFAULT 'general';

-- 3. 验证修改结果
SELECT 
    COLUMN_NAME,
    COLUMN_TYPE,
    IS_NULLABLE,
    COLUMN_DEFAULT
FROM information_schema.COLUMNS 
WHERE TABLE_NAME = 'chat_sessions' 
AND COLUMN_NAME = 'session_type';

-- 4. 显示当前会话类型分布
SELECT 
    session_type,
    COUNT(*) as count
FROM chat_sessions 
GROUP BY session_type 
ORDER BY count DESC;

-- 5. 更新现有数据（如果有需要的话）
-- 将现有的'general'类型会话中，根据标题或内容判断是否为mental类型
-- 这里暂时不自动更新，由业务逻辑决定会话类型

-- 6. 清理备份表（可选）
-- DROP TABLE IF EXISTS chat_sessions_backup_002;
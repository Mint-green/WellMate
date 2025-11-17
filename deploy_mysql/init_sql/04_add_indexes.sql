-- 为用户表添加索引以优化查询性能

-- 1. 为username字段添加索引（用于登录查询）
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- 2. 为uuid字段添加索引（用于用户查询）
CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);

-- 3. 为is_active字段添加索引（用于状态检查）
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 4. 为last_login字段添加索引（用于登录时间查询）
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);

-- 5. 复合索引：username + is_active（优化登录查询）
CREATE INDEX IF NOT EXISTS idx_users_username_active ON users(username, is_active);

-- 6. 复合索引：uuid + is_active（优化用户信息查询）
CREATE INDEX IF NOT EXISTS idx_users_uuid_active ON users(uuid, is_active);

-- 显示索引创建结果
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    SEQ_IN_INDEX
FROM information_schema.STATISTICS 
WHERE TABLE_NAME = 'users' 
ORDER BY INDEX_NAME, SEQ_IN_INDEX;
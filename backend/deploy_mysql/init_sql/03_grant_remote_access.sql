-- 授予远程访问权限（MySQL 8.0兼容版本）
-- 先创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'wellmateuser'@'%' IDENTIFIED BY 'wellmatepass';

-- 授予权限
GRANT ALL PRIVILEGES ON wellmate.* TO 'wellmateuser'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
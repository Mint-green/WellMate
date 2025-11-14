-- 插入测试用户数据
-- 密码: password123 (明文存储)
INSERT INTO users (username, password, full_name, gender, birth_date, age, settings, is_active) 
VALUES 
    ('testuser1', 'password123', '测试用户1', 'male', '1990-01-01', 33, NULL, TRUE),
    ('testuser2', 'password123', '测试用户2', 'female', '1995-05-15', 28, NULL, TRUE),
    ('testuser3', 'password123', '测试用户3', 'other', '2000-12-25', 23, NULL, TRUE);

-- 更新测试用户的最后登录时间为当前时间
UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username LIKE 'testuser%';
# 用户信息API设计文档

## 1. 概述

本文档描述了健康助手应用的用户信息API设计，包括用户注册、登录、登出和获取用户信息等功能。

## 2. 设计原则

- 提供注册、登录、登出等基本功能
- 实现账户激活状态检查
- 为简化实现，密码以明文形式存储

## 3. API接口设计

### 3.1 用户注册

**Endpoint**: `/api/user/auth/register`

**Method**: POST

**Request Body**:
```json
{
  "username": "用户名",
  "password": "密码",
  "full_name": "用户全名",
  "gender": "性别（可选）",
  "birth_date": "生日（可选）",
  "settings": "用户设置（可选，JSON格式）"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "用户注册成功",
  "user_id": "用户ID",
  "uuid": "用户UUID"
}
```

**错误响应**:
- 400: 请求参数缺失或格式错误
- 409: 用户名已存在
- 500: 服务器内部错误

### 3.2 用户登录

**Endpoint**: `/api/user/auth/login`

**Method**: POST

**Request Body**:
```json
{
  "username": "用户名",
  "password": "密码"
}
```

**Response**:
```json
{
  "status": "success",
  "user_id": "用户ID",
  "uuid": "用户UUID",
  "username": "用户名",
  "full_name": "用户全名"
}
```

**错误响应**:
- 400: 请求参数缺失或格式错误
- 401: 用户名或密码错误
- 403: 账户未激活
- 500: 服务器内部错误

### 3.3 用户登出

**Endpoint**: `/api/user/auth/logout`

**Method**: POST

**Response**:
```json
{
  "status": "success",
  "message": "登出成功"
}
```

**错误响应**:
- 500: 服务器内部错误

### 3.4 获取用户信息

**Endpoint**: `/api/user/auth/profile`

**Method**: GET

**Query Parameters**:
- uuid: 用户UUID（可选，与username二选一）
- username: 用户名（可选，与uuid二选一）

**Response**:
```json
{
  "status": "success",
  "user": {
    "id": "用户ID",
    "uuid": "用户UUID",
    "username": "用户名",
    "full_name": "用户全名",
    "gender": "性别",
    "birth_date": "生日",
    "age": "年龄",
    "settings": "用户设置（JSON格式）",
    "created_at": "账户创建时间",
    "last_login": "最后登录时间"
  }
}
```

**错误响应**:
- 500: 服务器内部错误

### 3.5 更新用户配置

**Endpoint**: `/api/user/auth/settings`

**Method**: PATCH

**Request Body**:
```json
{
  "uuid": "用户UUID（与username二选一）",
  "username": "用户名（与uuid二选一）",
  "settings": {
    "配置项1": "配置值1",
    "配置项2": "配置值2"
  }
}
```

**说明**:
- 此接口支持部分更新用户配置，只更新提供的配置项
- 如果某个配置项的值设置为null，则会删除该项配置
- 如果用户当前没有设置，则会初始化为空对象后再合并新设置

**Response**:
```json
{
  "status": "success",
  "message": "用户设置更新成功"
}
```

**错误响应**:
- 400: 请求参数缺失或格式错误
- 404: 用户不存在
- 500: 服务器内部错误

## 4. 用户信息表结构

### 4.1 users 表

| 字段名 | 数据类型 | 是否为空 | 默认值 | 说明 |
|--------|----------|----------|--------|------|
| id | INT | NOT NULL | AUTO_INCREMENT | 用户唯一标识 |
| uuid | VARCHAR(36) | NOT NULL |  | 用户UUID标识符 |
| username | VARCHAR(50) | NOT NULL |  | 用户名（登录用） |
| password | VARCHAR(50) | NOT NULL |  | 用户密码（明文存储） |
| full_name | VARCHAR(100) | NOT NULL |  | 用户全名 |
| gender | ENUM('male', 'female', 'other') | YES | NULL | 性别 |
| birth_date | DATE | YES | NULL | 生日 |
| age | INT | YES | NULL | 年龄 |
| settings | JSON | YES | NULL | 用户设置（JSON格式） |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 账户创建时间 |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 最后更新时间 |
| last_login | DATETIME | YES | NULL | 最后登录时间 |
| is_active | BOOLEAN | NOT NULL | TRUE | 账户是否激活 |

### 4.2 索引

- 主键: id
- 唯一索引: uuid
- 唯一索引: username
- 普通索引: created_at

## 5. 安全考虑

- 为简化实现，密码以明文形式存储
- 用户名和UUID设置为唯一，防止重复注册
- 重要的时间戳字段自动维护，防止篡改
- 敏感操作需要验证用户身份
- 实施适当的密码强度要求
- 对所有请求和响应进行日志记录，用于审计和调试

## 6. 错误处理

所有API端点都遵循统一的错误响应格式:
```json
{
  "error": {
    "code": "错误代码",
    "message": "错误描述信息",
    "details": "详细错误信息（可选）"
  }
}
```

常见的错误代码:
- INVALID_REQUEST: 请求参数无效
- AUTHENTICATION_FAILED: 身份验证失败
- USER_ALREADY_EXISTS: 用户已存在
- USER_NOT_FOUND: 用户不存在
- ACCOUNT_INACTIVE: 账户未激活
- INTERNAL_ERROR: 服务器内部错误
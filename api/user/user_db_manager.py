#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据库操作管理器
负责所有用户相关的数据库操作
"""

import uuid
import datetime
import logging
from typing import Dict, Optional, List, Any

from utils.db_connector import db_connector

logger = logging.getLogger(__name__)

class UserDBManager:
    """用户数据库操作管理器"""
    
    def __init__(self):
        self.table_name = "users"
    
    def create_user(self, username: str, password: str, full_name: str, 
                   gender: Optional[str] = None, birth_date: Optional[str] = None,
                   age: Optional[int] = None, settings: Optional[Dict] = None) -> Dict[str, Any]:
        """创建新用户"""
        
        # 检查用户名是否已存在
        if self.get_user_by_username(username):
            raise ValueError(f"用户名 '{username}' 已存在")
        
        # 生成UUID
        user_uuid = str(uuid.uuid4())
        
        # 构建插入SQL
        insert_query = f"""
        INSERT INTO {self.table_name} 
        (uuid, username, password, full_name, gender, birth_date, age, settings, created_at, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # 准备参数
        params = (
            user_uuid, username, password, full_name, gender, birth_date, age,
            self._serialize_settings(settings) if settings else None,
            datetime.datetime.now(), True
        )
        
        try:
            # 执行插入操作
            rows_affected = db_connector.execute_update(insert_query, params)
            
            if rows_affected > 0:
                # 获取新创建的用户ID
                user = self.get_user_by_username(username)
                if user:
                    logger.info(f"用户创建成功: {username} (ID: {user['id']})")
                    return user
                else:
                    raise Exception("用户创建成功但无法查询到新用户")
            else:
                raise Exception("用户创建失败，影响行数为0")
                
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            raise
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户信息"""
        query = f"""
        SELECT id, uuid, username, password, full_name, gender, birth_date, age, 
               settings, created_at, updated_at, last_login, is_active
        FROM {self.table_name} 
        WHERE username = %s AND is_active = TRUE
        """
        
        try:
            result = db_connector.execute_query(query, (username,))
            if result:
                user = result[0]
                user['settings'] = self._deserialize_settings(user['settings'])
                return user
            return None
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
    
    def get_user_by_uuid(self, user_uuid: str) -> Optional[Dict[str, Any]]:
        """根据UUID获取用户信息"""
        query = f"""
        SELECT id, uuid, username, password, full_name, gender, birth_date, age, 
               settings, created_at, updated_at, last_login, is_active
        FROM {self.table_name} 
        WHERE uuid = %s AND is_active = TRUE
        """
        
        try:
            result = db_connector.execute_query(query, (user_uuid,))
            if result:
                user = result[0]
                user['settings'] = self._deserialize_settings(user['settings'])
                return user
            return None
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户信息"""
        query = f"""
        SELECT id, uuid, username, password, full_name, gender, birth_date, age, 
               settings, created_at, updated_at, last_login, is_active
        FROM {self.table_name} 
        WHERE id = %s AND is_active = TRUE
        """
        
        try:
            result = db_connector.execute_query(query, (user_id,))
            if result:
                user = result[0]
                user['settings'] = self._deserialize_settings(user['settings'])
                return user
            return None
        except Exception as e:
            logger.error(f"查询用户失败: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        user = self.get_user_by_username(username)
        
        if not user:
            return None
        
        # 检查密码（当前为明文比较，实际应用中应使用哈希）
        if user['password'] != password:
            return None
        
        # 更新最后登录时间
        self.update_last_login(user['id'])
        
        return user
    
    def update_last_login(self, user_id: int) -> bool:
        """更新用户最后登录时间"""
        update_query = f"""
        UPDATE {self.table_name} 
        SET last_login = %s, updated_at = %s
        WHERE id = %s
        """
        
        try:
            current_time = datetime.datetime.now()
            rows_affected = db_connector.execute_update(
                update_query, (current_time, current_time, user_id)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {e}")
            return False
    
    def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """更新用户设置"""
        update_query = f"""
        UPDATE {self.table_name} 
        SET settings = %s, updated_at = %s
        WHERE id = %s
        """
        
        try:
            current_time = datetime.datetime.now()
            rows_affected = db_connector.execute_update(
                update_query, (self._serialize_settings(settings), current_time, user_id)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新用户设置失败: {e}")
            return False
    
    def update_user_profile(self, user_id: int, full_name: Optional[str] = None, 
                           gender: Optional[str] = None, birth_date: Optional[str] = None,
                           age: Optional[int] = None) -> bool:
        """更新用户基本信息"""
        # 构建动态更新SQL
        update_fields = []
        params = []
        
        if full_name is not None:
            update_fields.append("full_name = %s")
            params.append(full_name)
        
        if gender is not None:
            update_fields.append("gender = %s")
            params.append(gender)
        
        if birth_date is not None:
            update_fields.append("birth_date = %s")
            params.append(birth_date)
        
        if age is not None:
            update_fields.append("age = %s")
            params.append(age)
        
        if not update_fields:
            return False  # 没有要更新的字段
        
        update_fields.append("updated_at = %s")
        params.append(datetime.datetime.now())
        params.append(user_id)
        
        update_query = f"""
        UPDATE {self.table_name} 
        SET {', '.join(update_fields)}
        WHERE id = %s
        """
        
        try:
            rows_affected = db_connector.execute_update(update_query, tuple(params))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户（软删除）"""
        update_query = f"""
        UPDATE {self.table_name} 
        SET is_active = FALSE, updated_at = %s
        WHERE id = %s
        """
        
        try:
            rows_affected = db_connector.execute_update(
                update_query, (datetime.datetime.now(), user_id)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"删除用户失败: {e}")
            return False
    
    def user_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        return self.get_user_by_username(username) is not None
    
    def _serialize_settings(self, settings: Dict[str, Any]) -> str:
        """序列化设置字典为JSON字符串"""
        import json
        return json.dumps(settings, ensure_ascii=False)
    
    def _deserialize_settings(self, settings_str: Optional[str]) -> Dict[str, Any]:
        """反序列化JSON字符串为设置字典"""
        import json
        if not settings_str:
            return {}
        try:
            return json.loads(settings_str)
        except (json.JSONDecodeError, TypeError):
            return {}

# 创建全局实例
user_db_manager = UserDBManager()
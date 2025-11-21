# 用户数据模型（数据库版本）
from dataclasses import dataclass
from typing import Optional, Dict, Any
import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.db_connector import db_connector

@dataclass
class User:
    """用户数据模型"""
    id: int
    uuid: str
    username: str
    password: str
    full_name: str
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    age: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None
    is_active: bool = True

    def to_dict(self):
        """将用户对象转换为字典"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'full_name': self.full_name,
            'gender': self.gender,
            'birth_date': self.birth_date,
            'age': self.age,
            'settings': self.settings,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'last_login': self.last_login,
            'is_active': self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建用户对象"""
        return cls(
            id=data.get('id', 0),
            uuid=data.get('uuid', ''),
            username=data.get('username', ''),
            password=data.get('password', ''),
            full_name=data.get('full_name', ''),
            gender=data.get('gender'),
            birth_date=data.get('birth_date'),
            age=data.get('age'),
            settings=data.get('settings'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            last_login=data.get('last_login'),
            is_active=data.get('is_active', True)
        )

class UserDatabaseManager:
    """用户数据库管理类"""
    
    @staticmethod
    def create_user(username: str, password: str, full_name: str, gender: Optional[str] = None, 
                   birth_date: Optional[str] = None, age: Optional[int] = None, 
                   settings: Optional[Dict[str, Any]] = None) -> Optional[User]:
        """创建新用户"""
        # 检查用户是否已存在
        if UserDatabaseManager.get_user_by_username(username):
            return None
        
        # 插入新用户
        insert_query = """
        INSERT INTO users (uuid, username, password, full_name, gender, birth_date, age, settings) 
        VALUES (UUID(), %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            params = (username, password, full_name, gender, birth_date, age, settings)
            db_connector.execute_update(insert_query, params)
            
            # 获取刚创建的用户
            return UserDatabaseManager.get_user_by_username(username)
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
    
    @staticmethod
    def get_user_by_uuid(user_uuid: str) -> Optional[User]:
        """根据用户UUID获取用户"""
        query = "SELECT * FROM users WHERE uuid = %s"
        try:
            result = db_connector.execute_query(query, (user_uuid,))
            if result:
                return User.from_dict(result[0])
            return None
        except Exception as e:
            print(f"查询用户失败: {e}")
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """根据用户名获取用户"""
        query = "SELECT * FROM users WHERE username = %s"
        try:
            result = db_connector.execute_query(query, (username,))
            if result:
                return User.from_dict(result[0])
            return None
        except Exception as e:
            print(f"查询用户失败: {e}")
            return None
    
    @staticmethod
    def update_user_settings(uuid: str, settings: Dict[str, Any]) -> bool:
        """更新用户设置"""
        update_query = "UPDATE users SET settings = %s WHERE uuid = %s"
        try:
            db_connector.execute_update(update_query, (settings, uuid))
            return True
        except Exception as e:
            print(f"更新用户设置失败: {e}")
            return False
    
    @staticmethod
    def update_last_login(uuid: str) -> bool:
        """更新最后登录时间"""
        update_query = "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE uuid = %s"
        try:
            db_connector.execute_update(update_query, (uuid,))
            return True
        except Exception as e:
            print(f"更新最后登录时间失败: {e}")
            return False
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """验证用户身份"""
        query = "SELECT * FROM users WHERE username = %s AND password = %s AND is_active = TRUE"
        try:
            result = db_connector.execute_query(query, (username, password))
            if result:
                # 更新最后登录时间
                UserDatabaseManager.update_last_login(result[0]['uuid'])
                return User.from_dict(result[0])
            return None
        except Exception as e:
            print(f"用户认证失败: {e}")
            return None
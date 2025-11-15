# 用户数据模型
from dataclasses import dataclass
from typing import Optional, Dict, Any
import datetime

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

@dataclass
class LoginRequest:
    """登录请求数据模型"""
    username: str
    password: str

@dataclass
class RegisterRequest:
    """注册请求数据模型"""
    username: str
    password: str
    full_name: str
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    age: Optional[int] = None
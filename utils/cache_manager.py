#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器
提供内存缓存功能，减少数据库查询次数
"""

import time
import logging
from typing import Any, Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, default_ttl: int = 300):  # 默认5分钟
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                cache_item = self._cache[key]
                # 检查是否过期
                if time.time() < cache_item['expires_at']:
                    logger.debug(f"缓存命中: {key}")
                    return cache_item['value']
                else:
                    # 过期，删除缓存项
                    del self._cache[key]
                    logger.debug(f"缓存过期: {key}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        with self._lock:
            expires_at = time.time() + (ttl or self.default_ttl)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            logger.debug(f"缓存设置: {key}, TTL: {ttl or self.default_ttl}秒")
    
    def delete(self, key: str) -> bool:
        """删除缓存项"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"缓存删除: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.debug("缓存已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            current_time = time.time()
            active_items = {}
            expired_items = {}
            
            for key, item in self._cache.items():
                if current_time < item['expires_at']:
                    active_items[key] = item
                else:
                    expired_items[key] = item
            
            return {
                'total_items': len(self._cache),
                'active_items': len(active_items),
                'expired_items': len(expired_items),
                'memory_usage': sum(len(str(item)) for item in self._cache.values())
            }

# 全局缓存实例
cache_manager = CacheManager()

# 缓存键生成器
def generate_user_cache_key(username: str) -> str:
    """生成用户缓存键"""
    return f"user:{username}"

def generate_user_uuid_cache_key(uuid: str) -> str:
    """生成用户UUID缓存键"""
    return f"user_uuid:{uuid}"

def generate_user_id_cache_key(user_id: int) -> str:
    """生成用户ID缓存键"""
    return f"user_id:{user_id}"

# 缓存装饰器
def cache_result(ttl: int = 300, key_func: Optional[callable] = None):
    """缓存方法结果的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成键
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
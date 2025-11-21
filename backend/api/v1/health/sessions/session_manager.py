"""
会话管理器

提供对话会话的创建、查询、消息存储等数据库操作功能
"""

import logging
import datetime
from typing import Dict, List, Optional, Any

# 导入数据库连接器
try:
    from utils.db_connector import db_connector
except ImportError:
    # 如果无法导入，创建模拟连接器用于测试
    class MockDBConnector:
        def execute_query(self, query, params=None):
            print(f"模拟执行查询: {query}")
            return []
        
        def execute_update(self, query, params=None):
            print(f"模拟执行更新: {query}")
            return 1
    
    db_connector = MockDBConnector()

logger = logging.getLogger(__name__)

class SessionManager:
    """会话管理器类"""
    
    def __init__(self):
        self.db = db_connector
    
    def create_session(self, user_uuid: str, session_type: str = 'physical', title: str = None) -> Dict[str, Any]:
        """
        创建新会话
        
        Args:
            user_uuid: 用户UUID
            session_type: 会话类型（physical, mental, general）
            title: 会话标题
            
        Returns:
            dict: 创建的会话信息
        """
        try:
            # 生成会话ID和conversation_id
            import uuid
            session_id = str(uuid.uuid4())
            conversation_id = str(uuid.uuid4())
            
            # 如果没有提供标题，生成默认标题
            if not title:
                title = f"{session_type}健康咨询会话"
            
            # 首先尝试使用新方案（包含conversation_id字段）
            try:
                query = """
                    INSERT INTO chat_sessions (session_id, user_uuid, session_type, title, conversation_id, created_at, updated_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW(), TRUE)
                """
                
                params = (session_id, user_uuid, session_type, title, conversation_id)
                result = self.db.execute_update(query, params)
                
                if result > 0:
                    logger.info(f"创建会话成功（新方案）: user_uuid={user_uuid}, session_id={session_id}, conversation_id={conversation_id}")
                    return {
                        'session_id': session_id,
                        'user_uuid': user_uuid,
                        'session_type': session_type,
                        'title': title,
                        'conversation_id': conversation_id,
                        'created_at': datetime.datetime.now().isoformat(),
                        'is_active': True
                    }
                else:
                    logger.error(f"新方案创建会话失败，尝试旧方案: user_uuid={user_uuid}")
                    
            except Exception as new_scheme_error:
                logger.warning(f"新方案创建会话失败，尝试旧方案: {new_scheme_error}")
            
            # 回退到旧方案（不包含conversation_id字段）
            try:
                fallback_query = """
                    INSERT INTO chat_sessions (session_id, user_uuid, session_type, title, created_at, updated_at, is_active)
                    VALUES (%s, %s, %s, %s, NOW(), NOW(), TRUE)
                """
                
                fallback_params = (session_id, user_uuid, session_type, title)
                fallback_result = self.db.execute_update(fallback_query, fallback_params)
                
                if fallback_result > 0:
                    logger.info(f"创建会话成功（旧方案）: user_uuid={user_uuid}, session_id={session_id}")
                    return {
                        'session_id': session_id,
                        'user_uuid': user_uuid,
                        'session_type': session_type,
                        'title': title,
                        'conversation_id': conversation_id,  # 仍然返回conversation_id，但不会存储在数据库中
                        'created_at': datetime.datetime.now().isoformat(),
                        'is_active': True
                    }
                else:
                    logger.error(f"旧方案创建会话失败: user_uuid={user_uuid}")
                    return None
                    
            except Exception as fallback_error:
                logger.error(f"旧方案创建会话异常: {fallback_error}")
                return None
                
        except Exception as e:
            logger.error(f"创建会话异常: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 会话信息或None
        """
        try:
            query = """
                SELECT session_id, user_uuid, session_type, title, conversation_id, created_at, updated_at, is_active
                FROM chat_sessions 
                WHERE session_id = %s AND is_active = TRUE
            """
            
            result = self.db.execute_query(query, (session_id,))
            
            if result:
                session = result[0]
                # 检查返回格式：如果是字典格式，直接返回；如果是元组格式，需要转换
                if isinstance(session, dict):
                    # 已经是字典格式，直接返回
                    return {
                        'session_id': session['session_id'],
                        'user_uuid': session['user_uuid'],
                        'session_type': session['session_type'],
                        'title': session['title'],
                        'conversation_id': session['conversation_id'],
                        'created_at': session['created_at'].isoformat() if session['created_at'] else None,
                        'updated_at': session['updated_at'].isoformat() if session['updated_at'] else None,
                        'is_active': bool(session['is_active'])
                    }
                else:
                    # 元组格式，按索引访问
                    return {
                        'session_id': session[0],
                        'user_uuid': session[1],
                        'session_type': session[2],
                        'title': session[3],
                        'conversation_id': session[4],
                        'created_at': session[5].isoformat() if session[5] else None,
                        'updated_at': session[6].isoformat() if session[6] else None,
                        'is_active': bool(session[7])
                    }
            return None
                
        except Exception as e:
            logger.error(f"获取会话异常: {e}")
            return None
    
    def get_user_sessions(self, user_uuid: str, session_type: str = None) -> List[Dict[str, Any]]:
        """
        获取用户的所有会话
        
        Args:
            user_uuid: 用户UUID
            session_type: 过滤会话类型
            
        Returns:
            list: 会话列表
        """
        try:
            if session_type:
                query = """
                    SELECT session_id, user_uuid, session_type, title, conversation_id, created_at, updated_at, is_active
                    FROM chat_sessions 
                    WHERE user_uuid = %s AND session_type = %s AND is_active = TRUE
                    ORDER BY updated_at DESC
                """
                params = (user_uuid, session_type)
            else:
                query = """
                    SELECT session_id, user_uuid, session_type, title, conversation_id, created_at, updated_at, is_active
                    FROM chat_sessions 
                    WHERE user_uuid = %s AND is_active = TRUE
                    ORDER BY updated_at DESC
                """
                params = (user_uuid,)
            
            results = self.db.execute_query(query, params)
            
            sessions = []
            for row in results:
                # 检查返回格式：如果是字典格式，直接访问；如果是元组格式，按索引访问
                if isinstance(row, dict):
                    sessions.append({
                        'session_id': row['session_id'],
                        'user_uuid': row['user_uuid'],
                        'session_type': row['session_type'],
                        'title': row['title'],
                        'conversation_id': row['conversation_id'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                        'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                        'is_active': bool(row['is_active'])
                    })
                else:
                    sessions.append({
                        'session_id': row[0],
                        'user_uuid': row[1],
                        'session_type': row[2],
                        'title': row[3],
                        'conversation_id': row[4],
                        'created_at': row[5].isoformat() if row[5] else None,
                        'updated_at': row[6].isoformat() if row[6] else None,
                        'is_active': bool(row[7])
                    })
            
            return sessions
                
        except Exception as e:
            logger.error(f"获取用户会话异常: {e}")
            return []
    
    def add_message(self, session_id: str, message_type: str, content: str, metadata: Dict = None) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话ID
            message_type: 消息类型（user, assistant）
            content: 消息内容
            metadata: 元数据
            
        Returns:
            bool: 是否成功
        """
        try:
            # 序列化元数据
            metadata_json = None
            if metadata:
                import json
                metadata_json = json.dumps(metadata)
            
            # 插入消息记录
            query = """
                INSERT INTO chat_messages (session_id, message_type, content, timestamp, metadata)
                VALUES (%s, %s, %s, NOW(), %s)
            """
            
            params = (session_id, message_type, content, metadata_json)
            result = self.db.execute_update(query, params)
            
            if result > 0:
                # 更新会话的更新时间
                self.update_session_timestamp(session_id)
                logger.info(f"添加消息成功: session_id={session_id}, type={message_type}")
                return True
            else:
                logger.error(f"添加消息失败: session_id={session_id}")
                return False
                
        except Exception as e:
            logger.error(f"添加消息异常: {e}")
            return False
    
    def get_or_create_conversation_id(self, session_id: str) -> str:
        """
        获取或创建会话对应的conversation_id
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: conversation_id
        """
        try:
            # 首先尝试从chat_sessions表中获取conversation_id（新方案）
            try:
                query = """
                    SELECT conversation_id 
                    FROM chat_sessions 
                    WHERE session_id = %s AND conversation_id IS NOT NULL
                """
                
                result = self.db.execute_query(query, (session_id,))
                
                if result:
                    row = result[0]
                    conversation_id = row[0] if isinstance(row, tuple) else row['conversation_id']
                    if conversation_id:
                        logger.info(f"复用现有conversation_id: {conversation_id}")
                        return conversation_id
                
                # 如果没有找到有效的conversation_id，生成新的并尝试更新到数据库
                import uuid
                new_conversation_id = str(uuid.uuid4())
                
                # 尝试更新chat_sessions表中的conversation_id字段
                try:
                    update_query = """
                        UPDATE chat_sessions 
                        SET conversation_id = %s, updated_at = NOW() 
                        WHERE session_id = %s
                    """
                    
                    update_result = self.db.execute_update(update_query, (new_conversation_id, session_id))
                    
                    if update_result > 0:
                        logger.info(f"创建新conversation_id并更新到数据库: {new_conversation_id}")
                    else:
                        logger.warning(f"更新conversation_id到数据库失败，但仍返回新ID: {new_conversation_id}")
                    
                    return new_conversation_id
                    
                except Exception as update_error:
                    # 如果更新失败，可能是conversation_id字段不存在，回退到旧方案
                    logger.warning(f"新方案更新失败，回退到旧方案: {update_error}")
                    
            except Exception as new_scheme_error:
                # 如果新方案查询失败，可能是conversation_id字段不存在，回退到旧方案
                logger.warning(f"新方案查询失败，回退到旧方案: {new_scheme_error}")
            
            # 回退方案：从chat_messages表中获取最新的conversation_id（旧方案）
            fallback_query = """
                SELECT metadata 
                FROM chat_messages 
                WHERE session_id = %s AND metadata IS NOT NULL
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            
            fallback_result = self.db.execute_query(fallback_query, (session_id,))
            
            if fallback_result:
                row = fallback_result[0]
                metadata_json = row[0] if isinstance(row, tuple) else row['metadata']
                
                if metadata_json:
                    import json
                    try:
                        metadata = json.loads(metadata_json)
                        conversation_id = metadata.get('conversation_id')
                        if conversation_id:
                            logger.info(f"从消息元数据中复用conversation_id: {conversation_id}")
                            return conversation_id
                    except:
                        pass
            
            # 如果旧方案也失败，生成新的conversation_id
            import uuid
            new_conversation_id = str(uuid.uuid4())
            logger.info(f"生成新conversation_id: {new_conversation_id}")
            return new_conversation_id
                
        except Exception as e:
            logger.error(f"获取conversation_id异常: {e}")
            import uuid
            return str(uuid.uuid4())
    
    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取会话的消息列表
        
        Args:
            session_id: 会话ID
            limit: 消息数量限制
            
        Returns:
            list: 消息列表
        """
        try:
            query = """
                SELECT id, session_id, message_type, content, timestamp, metadata
                FROM chat_messages 
                WHERE session_id = %s
                ORDER BY timestamp ASC
                LIMIT %s
            """
            
            results = self.db.execute_query(query, (session_id, limit))
            
            messages = []
            for row in results:
                # 检查返回格式：如果是字典格式，直接访问；如果是元组格式，按索引访问
                if isinstance(row, dict):
                    # 解析元数据
                    metadata = None
                    if row['metadata']:
                        import json
                        try:
                            metadata = json.loads(row['metadata'])
                        except:
                            metadata = None
                    
                    messages.append({
                        'id': row['id'],
                        'session_id': row['session_id'],
                        'message_type': row['message_type'],
                        'content': row['content'],
                        'timestamp': row['timestamp'].isoformat() if row['timestamp'] else None,
                        'metadata': metadata
                    })
                else:
                    # 解析元数据
                    metadata = None
                    if row[5]:
                        import json
                        try:
                            metadata = json.loads(row[5])
                        except:
                            metadata = None
                    
                    messages.append({
                        'id': row[0],
                        'session_id': row[1],
                        'message_type': row[2],
                        'content': row[3],
                        'timestamp': row[4].isoformat() if row[4] else None,
                        'metadata': metadata
                    })
            
            return messages
                
        except Exception as e:
            logger.error(f"获取会话消息异常: {e}")
            return []
    
    def update_session_timestamp(self, session_id: str) -> bool:
        """
        更新会话时间戳
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        try:
            query = """
                UPDATE chat_sessions 
                SET updated_at = NOW() 
                WHERE session_id = %s
            """
            
            result = self.db.execute_update(query, (session_id,))
            return result > 0
                
        except Exception as e:
            logger.error(f"更新会话时间戳异常: {e}")
            return False
    
    def close_session(self, session_id: str) -> bool:
        """
        关闭会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功
        """
        try:
            query = """
                UPDATE chat_sessions 
                SET is_active = FALSE, updated_at = NOW() 
                WHERE session_id = %s
            """
            
            result = self.db.execute_update(query, (session_id,))
            
            if result > 0:
                logger.info(f"关闭会话成功: session_id={session_id}")
                return True
            else:
                logger.error(f"关闭会话失败: session_id={session_id}")
                return False
                
        except Exception as e:
            logger.error(f"关闭会话异常: {e}")
            return False

# 创建全局会话管理器实例
session_manager = SessionManager()
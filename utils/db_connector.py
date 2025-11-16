import mysql.connector
from config.db_config import DatabaseConfig
import logging
import threading
from typing import Optional

class DatabaseConnector:
    """高性能数据库连接器 - 使用连接池和连接复用"""
    
    def __init__(self):
        """初始化数据库连接器"""
        self._connection_pool = None
        self._connection_params = None
        self._lock = threading.Lock()
        self._init_connection_pool()
        logging.info("高性能数据库连接器初始化完成")
    
    def _init_connection_pool(self):
        """初始化连接池"""
        if self._connection_pool is None:
            with self._lock:
                if self._connection_pool is None:
                    try:
                        # 获取连接参数并启用连接池
                        params = DatabaseConfig.get_connection_params()
                        params['port'] = int(params['port'])
                        
                        # 优化连接参数，增加超时时间以适应网络延迟
                        params.update({
                            'connect_timeout': 15,          # 连接超时增加到15秒
                            'connection_timeout': 30,       # 操作超时增加到30秒
                            'buffered': True,
                            'auth_plugin': 'mysql_native_password',
                            'use_pure': True
                        })
                        
                        # 连接池配置（使用mysql.connector支持的参数）
                        pool_params = {
                            'pool_name': 'wellmate_pool',
                            'pool_size': 3,                 # 减少连接池大小，避免超过MySQL最大连接数
                            'pool_reset_session': True
                        }
                        
                        # 合并连接参数和连接池参数
                        params.update(pool_params)
                        
                        self._connection_params = params
                        
                        # 创建连接池
                        self._connection_pool = mysql.connector.pooling.MySQLConnectionPool(**params)
                        logging.info(f"数据库连接池初始化成功，池大小: {params['pool_size']}")
                        
                    except Exception as e:
                        logging.error(f"连接池初始化失败: {e}")
                        # 降级为直接连接
                        self._connection_pool = None
    
    def get_connection(self, max_retries=2, retry_delay=1.0):
        """获取数据库连接（使用连接池）"""
        if self._connection_pool:
            # 使用连接池
            retry_count = 0
            while retry_count <= max_retries:
                try:
                    connection = self._connection_pool.get_connection()
                    if connection.is_connected():
                        # 验证连接是否有效
                        try:
                            cursor = connection.cursor()
                            cursor.execute("SELECT 1")
                            cursor.close()
                            return connection
                        except mysql.connector.Error:
                            # 连接无效，关闭并重试
                            connection.close()
                            raise mysql.connector.Error("Connection is not valid")
                except mysql.connector.Error as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        error_msg = str(e)
                        if "Too many connections" in error_msg:
                            logging.warning(f"连接数过多，等待后重试 (第{retry_count}次): {e}")
                            import time
                            time.sleep(retry_delay * 2)  # 连接数过多时等待更长时间
                        else:
                            logging.warning(f"从连接池获取连接失败，第{retry_count}次重试: {e}")
                            import time
                            time.sleep(retry_delay)
                    else:
                        logging.error(f"从连接池获取连接失败，已达到最大重试次数: {e}")
                        # 连接池失败时降级到直接连接
                        break
        
        # 连接池不可用或失败，使用直接连接（降级方案）
        return self._get_direct_connection(max_retries, retry_delay)
    
    def _get_direct_connection(self, max_retries=1, retry_delay=0.5):
        """获取直接连接（降级方案）"""
        retry_count = 0
        while retry_count <= max_retries:
            try:
                # 使用优化后的连接参数
                params = self._connection_params.copy() if self._connection_params else DatabaseConfig.get_connection_params()
                params.update({
                    'connect_timeout': 15,
                    'connection_timeout': 30,
                    'buffered': True,
                    'auth_plugin': 'mysql_native_password',
                    'use_pure': True
                })
                
                connection = mysql.connector.connect(**params)
                if connection.is_connected():
                    logging.info("直接数据库连接成功")
                    return connection
            except mysql.connector.Error as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logging.warning(f"直接连接失败，第{retry_count}次重试: {e}")
                    import time
                    time.sleep(retry_delay)
                else:
                    logging.error(f"直接连接失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                logging.error(f"创建直接连接失败: {e}")
                raise
    
    def execute_query(self, query, params=None):
        """执行查询语句"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Exception as e:
            logging.error(f"查询执行失败: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def execute_update(self, query, params=None):
        """执行更新语句（INSERT, UPDATE, DELETE）"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"更新执行失败: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def execute_transaction(self, queries_and_params):
        """执行事务操作"""
        connection = None
        try:
            connection = self.get_connection()
            connection.start_transaction()
            cursor = connection.cursor()
            
            for query, params in queries_and_params:
                cursor.execute(query, params)
            
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"事务执行失败: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

# 全局数据库连接实例
db_connector = DatabaseConnector()
# EOF
# mv /app/utils/db_connector.py.fixed /app/utils/db_connector.py
# echo "已修复db_connector.py文件"
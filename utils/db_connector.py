# docker exec -it well-mate-backend bash -c "cat > /app/utils/db_connector.py.fixed << 'EOF'
import mysql.connector
from config.db_config import DatabaseConfig
import logging

class DatabaseConnector:
    """数据库连接工具类 - 使用直接连接而不是连接池"""
    
    def __init__(self):
        """初始化数据库连接器"""
        self._connection_params = None
        logging.info("数据库连接器初始化完成")
    
    def _get_connection_params(self):
        """获取连接参数"""
        if not self._connection_params:
            # 获取连接参数
            params = DatabaseConfig.get_connection_params()
            # 移除连接池相关参数
            params.pop('pool_name', None)
            params.pop('pool_size', None)
            # 确保端口是整数
            params['port'] = int(params['port'])
            # 优化连接超时参数，减少网络等待时间
            params.update({
                'connect_timeout': 5,        # 连接超时从10秒减少到5秒
                'connection_timeout': 15,     # 连接超时从30秒减少到15秒
                'buffered': True,
                'auth_plugin': 'mysql_native_password',  # 明确指定认证插件
                'use_pure': True              # 使用纯Python实现，避免C扩展问题
            })
            self._connection_params = params
        return self._connection_params

    def get_connection(self, max_retries=2, retry_delay=1):
        """获取数据库连接，支持重试机制"""
        connection = None
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                connection_params = self._get_connection_params()
                logging.info(f"尝试连接到数据库: {connection_params['host']}:{connection_params['port']}")
                connection = mysql.connector.connect(**connection_params)
                if connection.is_connected():
                    logging.info("数据库连接成功")
                    return connection
            except mysql.connector.Error as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logging.warning(f"数据库连接失败，第{retry_count}次重试: {e}")
                    import time
                    time.sleep(retry_delay)
                else:
                    logging.error(f"数据库连接失败，已达到最大重试次数: {e}")
                    raise
            except Exception as e:
                logging.error(f"创建数据库连接失败: {e}")
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
import os
from dotenv import load_dotenv

# 加载环境变量 - 适配本地调试和生产环境
env_file_path = os.path.join(os.path.dirname(__file__), '..', '.env')
env_local_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')

if os.path.exists(env_local_path):
    # 本地调试模式：优先加载.env.local，然后加载.env
    load_dotenv(env_local_path)
    load_dotenv(env_file_path)
else:
    # 生产环境模式：只加载.env
    load_dotenv(env_file_path)

class DatabaseConfig:
    """数据库配置类"""
    
    # 数据库连接配置
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'wellmateuser')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'wellmatepass')
    DB_NAME = os.getenv('DB_NAME', 'wellmate')
    
    # 数据库连接池配置
    DB_POOL_NAME = os.getenv('DB_POOL_NAME', 'wellmate_pool')
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))
    
    @classmethod
    def get_connection_params(cls):
        """获取数据库连接参数"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'charset': 'utf8mb4',
            'autocommit': True,
            'pool_name': cls.DB_POOL_NAME,
            'pool_size': cls.DB_POOL_SIZE
        }
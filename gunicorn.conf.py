# Gunicorn配置文件
import os
from dotenv import load_dotenv

# 加载环境变量 - 生产环境只加载.env文件
import os
env_file_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file_path)

# 从环境变量获取配置，如果没有则使用默认值
host = os.getenv('HOST', '0.0.0.0')
port = os.getenv('PORT', '5000')

# 绑定的主机和端口
bind = f'{host}:{port}'

# 工作进程数，调整为更保守的设置
workers = int(os.getenv('GUNICORN_WORKERS', '2'))

# 每个工作进程的线程数
threads = int(os.getenv('GUNICORN_THREADS', '1'))

# 工作进程类型
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')

# 请求超时时间（秒）
timeout = int(os.getenv('GUNICORN_TIMEOUT', '60'))

# 访问日志格式
accesslog = 'logs/access.log'  # 输出到访问日志文件
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 错误日志格式和级别
errorlog = 'logs/error.log'  # 输出到错误日志文件
loglevel = os.getenv('LOG_LEVEL', 'debug')  # 设置为debug级别以获取更详细日志

# 进程ID文件
# pidfile = 'gunicorn.pid'

# 守护进程模式（生产环境可以设置为True）
daemon = os.getenv('GUNICORN_DAEMON', 'False').lower() == 'true'

# 最大请求数，超过后重启工作进程
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '50'))

# 环境变量
raw_env = [
    f'FLASK_ENV={os.getenv("FLASK_ENV", "production")}',
    f'DEBUG={os.getenv("DEBUG", "False")}',
    # SECRET_KEY当前项目不需要，已移除
]
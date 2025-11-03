# Gunicorn配置文件

# 绑定的主机和端口
bind = '0.0.0.0:8000'

# 工作进程数，通常设置为CPU核心数的2-4倍
workers = 4

# 每个工作进程的线程数
threads = 2

# 工作进程类型
worker_class = 'gevent'

# 请求超时时间（秒）
timeout = 30

# 访问日志格式
accesslog = '-'  # 输出到标准输出
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 错误日志格式和级别
errorlog = '-'  # 输出到标准输出
loglevel = 'info'

# 进程ID文件
# pidfile = 'gunicorn.pid'

# 守护进程模式（生产环境可以设置为True）
daemon = False

# 最大请求数，超过后重启工作进程
max_requests = 1000
max_requests_jitter = 50

# 环境变量
raw_env = [
    'FLASK_ENV=production',
    'DEBUG=False',
]
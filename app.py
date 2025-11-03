import os
from flask import Flask
from api import register_blueprints
from dotenv import load_dotenv

# 加载环境变量 - 适配本地调试和Docker容器环境
env_file_path = os.path.join(os.path.dirname(__file__), '.env')
env_local_path = os.path.join(os.path.dirname(__file__), '.env.local')

if os.path.exists(env_local_path):
    # 本地调试模式：优先加载.env.local，然后加载.env
    load_dotenv(env_local_path)
    load_dotenv(env_file_path)  # .env中的配置会覆盖.env.local中的相同变量
else:
    # 生产环境模式：只加载.env
    load_dotenv(env_file_path)

# 创建Flask应用实例
app = Flask(__name__)

# 配置应用（当前项目不需要SECRET_KEY，移除相关配置）
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'

# 注册所有蓝图
register_blueprints(app)

if __name__ == '__main__':
    # 从环境变量获取配置，如果没有则使用默认值
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # 运行Flask应用
    app.run(debug=debug, host=host, port=port)
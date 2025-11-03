from flask import Flask
from api import register_blueprints

# 创建Flask应用实例
app = Flask(__name__)

# 注册所有蓝图
register_blueprints(app)

if __name__ == '__main__':
    # 运行Flask应用，开启调试模式
    app.run(debug=True, host='0.0.0.0', port=5000)
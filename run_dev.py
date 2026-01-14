

from function.template import template_bp
from function.user_control import user_control_bp
from function.print_paiwei import print_paiwei_bp
from function.payment_gateway import payment_bp
from function.api import api_bp
from function.config import login_manager
from function.web_socket import socketio
from models import db
from flask import Flask,render_template,jsonify
from flask_login import login_required
from function.twilio_service import twilio_bp
from _token import SECRET_KEY  # 导入你的 SECRET_KEY 变量

#payment_gateway
# ✅ 创建 Flask 应用
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ✅ 配置数据库连接（⚠️ 这部分必须在 `db.init_app(app)` 之前）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://yukang:Lowyihong123@127.0.0.1/FAHUI'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # 这里必须调用
# ✅ 初始化 Flask-Login
login_manager.init_app(app)

# ✅ 注册蓝图
app.register_blueprint(template_bp, url_prefix='/template')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(user_control_bp, url_prefix='/user_control')
app.register_blueprint(print_paiwei_bp, url_prefix='/print_paiwei')
app.register_blueprint(payment_bp, url_prefix='/payment')
app.register_blueprint(twilio_bp, url_prefix='/twilio_service')



socketio.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5015, debug=True)

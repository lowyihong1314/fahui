from flask_login import LoginManager,current_user
from models.user_data import User  # 引入数据库 & 用户模型
from functools import wraps
from flask import jsonify,redirect,url_for,session,request
from models.fahui import Order  # 确保你导入了 Order 模型

import os

# 获取当前文件的绝对路径 (__file__ 是当前 Python 文件本身)
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定位到上一级目录
parent_dir = os.path.dirname(current_dir)

# 拼接进入 'database' 文件夹
data_path = os.path.join(parent_dir, 'database')


# 初始化 Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'user_control.login'

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # 通过 ID 加载用户

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('user_control.login'))  # 或其他登录页地址

            # 打印当前用户名
            if current_user.username:
                print(current_user.username)

            if not current_user.permissions or permission not in current_user.permissions:
                message = (f'No permission on this route for : {current_user.username}')
                print (message)
                return jsonify({"status": "error", "message": message})
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verification_required(order_id_arg_name='order_id'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 已登录用户直接放行
            if current_user.is_authenticated:
                return f(*args, **kwargs)

            order_id = kwargs.get(order_id_arg_name)
            if not order_id:
                return "❌ 缺少订单 ID", 400

            # 从 session 获取已验证过的手机号
            verified_phones = session.get('verified_phones', [])
            verified_orders = session.get('verified_orders', {})  # {order_id: phone}

            phone = None

            # 先看 session 缓存里有没有
            if str(order_id) in verified_orders:
                phone = verified_orders[str(order_id)]
            else:
                # 没缓存才查数据库
                order = Order.query.filter_by(id=order_id).first()
                if not order:
                    return "❌ 找不到订单", 404
                phone = order.phone
                # 缓存起来
                verified_orders[str(order_id)] = phone
                session['verified_orders'] = verified_orders

            # 判断手机号是否已经验证过
            if phone in verified_phones:
                return f(*args, **kwargs)
            else:
                return redirect(url_for(
                    'twilio.verification_page',
                    order_id=order_id
                ))

        return decorated_function
    return decorator

from flask_login import LoginManager,current_user
from app.models.user_data import User  # 引入数据库 & 用户模型
from functools import wraps
from flask import jsonify,redirect,url_for,session,request
from app.models.fahui import Order  # 确保你导入了 Order 模型
from app.extensions import login_manager
import os


# 当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# current_dir/../../
flask_path = os.path.abspath(
    os.path.join(current_dir, "..", "..")
)

# current_dir/../database
data_path = os.path.abspath(
    os.path.join(current_dir, "..", "database")
)

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({
        "status": "error",
        "message": "please login"
    }), 401

READ_ONLY_ORDER_VERSIONS = {"YLP_2024", "YLP_2025"}

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # 通过 ID 加载用户

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            # 未登录
            if not current_user.is_authenticated:
                return jsonify({
                    "status": "error",
                    "message": "please login"
                }), 401

            # 打印当前用户名（调试用）
            if current_user.username:
                print(current_user.username)

            # 无权限
            if not current_user.permissions or permission not in current_user.permissions:
                message = f'No permission on this route for: {current_user.username}'
                print(message)

                return jsonify({
                    "status": "error",
                    "message": message
                }), 403

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

#function/user_control.py
from flask import Blueprint,jsonify,request
from flask_login import login_user, login_required, logout_user, current_user
from app.models.user_data import User
from flask import session
from app.function.common import permission_required
from app.function.user_control.service import UserControlService

user_control_bp = Blueprint('user_control', __name__)

@user_control_bp.before_app_request
def check_login_version():
    if current_user.is_authenticated:
        session_version = session.get('login_version')
        if session_version is None or session_version != current_user.login_version:
            # 强制登出
            logout_user()
            session.pop('login_version', None)

            return jsonify({
                "status": "error",
                "message": "please login"
            }), 401
        

@user_control_bp.route('/get_user_data', methods=['GET'])
@login_required
def get_user_data():
    return jsonify(UserControlService.get_current_user_payload())

@user_control_bp.route('/get_all_user_data', methods=['GET'])
def get_all_user_data():
    users = User.query.all()
    user_data = [user.to_dict() for user in users]
    return jsonify(user_data)

@user_control_bp.route('/get_all_user_data_full', methods=['GET'])
def get_all_user_data_full():
    users = User.query.all()
    user_data = [user.to_dict() for user in users]
    return jsonify(user_data)

@user_control_bp.route('/edit_user_data', methods=['POST'])
@login_required
def edit_user_data():
    try:
        payload, status_code = UserControlService.update_current_user(request.get_json() or {})
        return jsonify(payload), status_code

    except Exception as e:
        from app.extensions import db

        db.session.rollback()
        return jsonify({"status": "error", "message": f"更新失败: {str(e)}"}), 500


@user_control_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"status": "success"}), 200  # 根据你的登录页函数名称修改

@user_control_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            "status": "error",
            "message": "用户名和密码不能为空"
        }), 400

    payload, status_code = UserControlService.authenticate(username, password)
    return jsonify(payload), status_code


# def is_safe_url(target):
#     from urllib.parse import urlparse, urljoin
#     host_url = urlparse(request.host_url)
#     redirect_url = urlparse(urljoin(request.host_url, target))
#     return redirect_url.scheme in ('http', 'https') and host_url.netloc == redirect_url.netloc


@user_control_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    payload, status_code = UserControlService.change_password(request.json or {})
    return jsonify(payload), status_code

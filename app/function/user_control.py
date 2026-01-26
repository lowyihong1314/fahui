#function/user_control.py
from flask import Blueprint,abort,send_file,jsonify,request,redirect,render_template,url_for,flash
from flask_login import login_user, login_required, logout_user, current_user
from app.extensions import db
from app.models.user_data import User,Notification
from datetime import timedelta,datetime
from flask import session
import json
from app.function.config import permission_required

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
    return jsonify({
        "status": "success",
        "user": current_user.to_dict()
    })

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
        data = request.get_json()

        # 确保 current_user 可用（假设使用 flask-login）
        user = User.query.get(current_user.id)
        if not user:
            return jsonify({"status": "error", "message": "用户不存在"}), 404

        # 允许修改的字段
        editable_fields = ['display_name', 'email', 'phone', 'user_theme']

        for field in editable_fields:
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()

        return jsonify({"status": "success", "message": "用户信息更新成功"})

    except Exception as e:
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

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user, remember=True, duration=timedelta(days=7))
        session['login_version'] = user.login_version

        return jsonify({
            "status": "success",
            "user": user.to_dict()
        })

    return jsonify({
        "status": "error",
        "message": "用户名或密码错误"
    }), 401


# def is_safe_url(target):
#     from urllib.parse import urlparse, urljoin
#     host_url = urlparse(request.host_url)
#     redirect_url = urlparse(urljoin(request.host_url, target))
#     return redirect_url.scheme in ('http', 'https') and host_url.netloc == redirect_url.netloc


@user_control_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"status": "error", "message": "旧密码和新密码不能为空"}), 400

    if not current_user.check_password(old_password):
        return jsonify({"status": "error", "message": "旧密码错误"}), 403

    current_user.set_password(new_password)
    current_user.increment_login_version()  # 版本+1，登出其他设备
    db.session.commit()

    # 更新当前 session 版本，保持当前设备继续登录
    session['login_version'] = current_user.login_version

    return jsonify({"status": "success", "message": "密码修改成功"}), 200

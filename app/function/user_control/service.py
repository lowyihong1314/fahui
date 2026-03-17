from datetime import timedelta

from flask import session
from flask_login import current_user, login_user

from app.extensions import db
from app.models.user_data import User


class UserControlService:
    @staticmethod
    def get_current_user_payload():
        return {
            "status": "success",
            "user": current_user.to_dict(),
        }

    @staticmethod
    def update_current_user(data: dict):
        user = User.query.get(current_user.id)
        if not user:
            return {"status": "error", "message": "用户不存在"}, 404

        for field in ["display_name", "email", "phone", "user_theme"]:
            if field in data:
                setattr(user, field, data[field])

        db.session.commit()
        return {"status": "success", "message": "用户信息更新成功"}, 200

    @staticmethod
    def authenticate(username: str, password: str):
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True, duration=timedelta(days=7))
            session["login_version"] = user.login_version
            return {"status": "success", "user": user.to_dict()}, 200

        return {"status": "error", "message": "用户名或密码错误"}, 401

    @staticmethod
    def change_password(data: dict):
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            return {"status": "error", "message": "旧密码和新密码不能为空"}, 400

        if not current_user.check_password(old_password):
            return {"status": "error", "message": "旧密码错误"}, 403

        current_user.set_password(new_password)
        current_user.increment_login_version()
        db.session.commit()
        session["login_version"] = current_user.login_version
        return {"status": "success", "message": "密码修改成功"}, 200

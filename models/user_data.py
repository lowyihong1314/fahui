# models/user_data.py
from app.extensions import db
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Enum
from sqlalchemy.ext.mutable import MutableList

class User(db.Model, UserMixin):
    __tablename__ = 'user_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=True)  # 新增字段，允许为空
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    department = db.Column(MutableList.as_mutable(db.JSON), default=[])
    permissions = db.Column(MutableList.as_mutable(db.JSON), default=[])

    user_theme = db.Column(db.String(20), nullable=False, default='light')  # 新增用户主题字段，默认light

    login_version = db.Column(db.Integer, default=0)

    def increment_login_version(self):
        self.login_version += 1
        
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,  # 加入到字典中
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
            "permissions": self.permissions,
            "user_theme": self.user_theme  # 新增返回主题信息
        }
    def to_dict_sort(self):
        return {
            "username": self.username,
            "display_name": self.display_name,
            "phone": self.phone
        }
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.id}, Username: {self.username}, DisplayName: {self.display_name}, Theme: {self.user_theme}>'

class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_department = db.Column(db.String(100), nullable=True)
    from_user_id = db.Column(db.Integer, nullable=True)
    from_username = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(100), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    href = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)
    create_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.id} - {self.username} - {self.is_read}>'


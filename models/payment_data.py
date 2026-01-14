from models import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Time, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import current_user

class PaymentData(db.Model):
    __tablename__ = 'payment_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_mode = db.Column(db.String(50))  # 新增字段
    valid_by = db.Column(db.String(100))
    valid_at = db.Column(db.DateTime)
    document = db.Column(db.String(255))

    # 可选：设置订单的反向引用
    order = db.relationship('Order', back_populates='payments')

    def to_dict_full(self):
        # 👇 计算 total_price_2
        total_price_2 = 0
        if self.order:
            for item in self.order.order_items:
                item_dict = item.to_dict()
                total_price_2 += item_dict.get("price", 0) or 0

        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'order_id': self.order_id,
            'total_price_old': float(self.total_price) if self.total_price is not None else None,
            'total_price': total_price_2,  # 👈 新增字段
            'status': self.status,
            'payment_mode': self.payment_mode,
            'valid_by': self.valid_by,
            'valid_at': self.valid_at.isoformat() if self.valid_at else None,
            'document': self.document,
            'order': self.order.to_all_detail() if self.order else None,
            "login": True if current_user and current_user.is_authenticated else False
        }
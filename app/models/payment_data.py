from app.extensions import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Time, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import current_user
from app.services.order_service import OrderService

class PaymentData(db.Model):
    __tablename__ = 'payment_data'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')
    payment_mode = db.Column(db.String(50))
    valid_by = db.Column(db.String(100))
    valid_at = db.Column(db.DateTime)
    document = db.Column(db.String(255))

    order = db.relationship('Order', back_populates='payments')

    def __repr__(self):
        return f"<PaymentData id={self.id} order_id={self.order_id}>"

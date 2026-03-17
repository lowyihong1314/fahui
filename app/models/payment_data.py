from app.extensions import db
from datetime import datetime

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

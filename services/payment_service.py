# services/payment_service.py

from flask_login import current_user
from models.payment_data import PaymentData
from services.order_service import OrderService
from services.order_item_service import OrderItemService


class PaymentService:
    """Payment 相关业务与序列化"""

    @staticmethod
    def calc_total_price_from_items(order) -> int:
        total = 0
        for item in order.order_items:
            item_dict = OrderItemService.to_dict(item)
            total += item_dict.get("price", 0) or 0
        return total

    @staticmethod
    def to_dict_full(payment: PaymentData) -> dict:
        order = payment.order

        total_price_2 = (
            PaymentService.calc_total_price_from_items(order)
            if order else 0
        )

        return {
            "id": payment.id,
            "created_at": payment.created_at.isoformat() if payment.created_at else None,
            "order_id": payment.order_id,
            "total_price_old": float(payment.total_price) if payment.total_price is not None else None,
            "total_price": total_price_2,
            "status": payment.status,
            "payment_mode": payment.payment_mode,
            "valid_by": payment.valid_by,
            "valid_at": payment.valid_at.isoformat() if payment.valid_at else None,
            "document": payment.document,
            "order": OrderService.to_all_detail(order) if order else None,
            "login": bool(current_user and current_user.is_authenticated)
        }

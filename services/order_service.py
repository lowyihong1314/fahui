# services/order_service.py

from flask_login import current_user
from models.fahui import Order


class OrderService:
    """Order 相关的所有业务逻辑"""

    # ========= 内部工具方法 =========

    @staticmethod
    def _get_latest_payment(order: Order):
        if not order.payments:
            return None
        return max(order.payments, key=lambda p: p.created_at)

    @staticmethod
    def _get_payment_status(order: Order) -> str:
        latest_payment = OrderService._get_latest_payment(order)
        return latest_payment.status if latest_payment else "Not-ready"

    @staticmethod
    def _format_created_at(order: Order):
        return (
            order.created_at.strftime('%y-%m-%d_%H:%M')
            if order.created_at else None
        )

    # ========= 对外方法 =========

    @staticmethod
    def to_dict(order: Order) -> dict:
        """原 Order.to_dict"""

        return {
            "id": order.id,
            "status": OrderService._get_payment_status(order),
            "name": order.name,
            "email": order.email,
            "customer_name": order.customer_name,
            "member_name": order.member_name,
            "phone": order.phone,
            "created_at": OrderService._format_created_at(order),
            "version": order.version,
            "login": bool(current_user and current_user.is_authenticated)
        }

    @staticmethod
    def to_all_detail(order: Order) -> dict:
        from services.order_item_service import OrderItemService

        order_data = OrderService.to_dict(order)

        order_data["order_items"] = [
            OrderItemService.to_all_detail(item)
            for item in order.order_items
        ]

        # 前一单 / 后一单
        prev_order = (
            Order.query
            .filter(Order.id < order.id)
            .order_by(Order.id.desc())
            .first()
        )

        next_order = (
            Order.query
            .filter(Order.id > order.id)
            .order_by(Order.id.asc())
            .first()
        )

        order_data["prev_id"] = prev_order.id if prev_order else None
        order_data["next_id"] = next_order.id if next_order else None

        return order_data

    @staticmethod
    def get_order_data_by_version(version: int) -> list[dict]:
        """原 Order.get_order_data_by_version"""

        orders = Order.query.filter_by(version=version).all()
        return [OrderService.to_dict(order) for order in orders]

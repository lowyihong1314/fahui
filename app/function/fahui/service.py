from app.extensions import db, socketio
from app.models import Order
from app.services.order_service import OrderService
from app.services.order_version_service import ACTIVE_ORDER_VERSION, OrderVersionService
from flask import session
from flask_login import current_user


class FahuiService:
    @staticmethod
    def _serialize_realtime_order(order: Order):
        return {
            "id": order.id,
            "status": OrderService._get_payment_status(order),
            "name": order.name,
            "customer_name": order.customer_name,
            "phone": order.phone,
            "created_at": OrderService._format_created_at(order),
            "version": order.version,
        }

    @staticmethod
    def search_orders(version: int, value: str, page: int, per_page: int):
        normalized_version = OrderVersionService.normalize(version)
        if not normalized_version:
            raise ValueError("version is required")

        return OrderService.search_orders(
            version=normalized_version,
            value=value,
            page_num=page,
            per_page=per_page,
        )

    @staticmethod
    def get_order_detail(order_id: int):
        return OrderService.to_all_detail(order_id)

    @staticmethod
    def get_orders_by_phone(phone: str):
        phone = (phone or "").strip()
        if not phone:
            return {
                "status": "error",
                "message": "phone is required",
            }, 400

        verified_phones = session.get("verified_phones", [])
        session_phone = session.get("phone")
        is_login = bool(current_user and current_user.is_authenticated)
        is_verified_owner = phone == session_phone or phone in verified_phones

        if not is_login and not is_verified_owner:
            return {
                "status": "error",
                "message": "请先完成手机验证",
            }, 403

        orders = (
            db.session.query(Order)
            .filter(Order.phone == phone)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .all()
        )

        return {
            "status": "success",
            "data": {
                "phone": phone,
                "items": [OrderService.to_dict(order) for order in orders],
            },
        }, 200

    @staticmethod
    def create_customer(data: dict):
        name = data.get("name")
        phone = data.get("phone")
        version = ACTIVE_ORDER_VERSION

        existing_order = (
            db.session.query(Order)
            .filter(
                Order.name == name,
                Order.phone == phone,
                Order.version == version,
            )
            .first()
        )

        if existing_order:
            return {
                "success": True,
                "message": "订单已存在",
                "order": OrderService.to_dict(existing_order),
                "duplicated": True,
            }

        new_order = Order(
            email=data.get("email"),
            name=name,
            customer_name=data.get("customer_name"),
            member_name=data.get("member_name"),
            phone=phone,
            version=version,
        )

        db.session.add(new_order)
        db.session.commit()

        socketio.emit(
            "fahui:order_created",
            {
                "order": FahuiService._serialize_realtime_order(new_order),
                "source": "new_customer",
            },
        )

        return {
            "success": True,
            "message": "订单已创建",
            "order": OrderService.to_dict(new_order),
            "duplicated": False,
        }

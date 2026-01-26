# services/order_service.py

from flask_login import current_user
from app.models.fahui import Order,ItemFormData,OrderItem
from sqlalchemy import or_
from app.extensions import db
from sqlalchemy.orm import joinedload
from flask import session

class OrderService:
    @staticmethod
    def search_orders(
        version: int,
        value: str,
        page_num: int = 1,
        per_page: int = 20
    ):
        query = (
            db.session.query(Order)
            .options(
                joinedload(Order.order_items)
                .joinedload(OrderItem.item_form_data)
            )
            .outerjoin(OrderItem, OrderItem.order_id == Order.id)
            .outerjoin(ItemFormData, ItemFormData.item_id == OrderItem.id)
            .filter(Order.version == version)
        )

        if value and value.strip():
            like_value = f"%{value.strip()}%"
            query = query.filter(
                or_(
                    Order.name.ilike(like_value),
                    Order.customer_name.ilike(like_value),
                    Order.phone.ilike(like_value),
                    ItemFormData.field_value.ilike(like_value),
                )
            )

        query = query.distinct(Order.id)

        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page_num,
            per_page=per_page,
            error_out=False
        )

        return {
            "items": [OrderService.to_dict(order) for order in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            }
        }
    # ========= 内部方法 =========

    @staticmethod
    def _build_search_query(version: int, value: str):
        query = (
            db.session.query(Order)
            .outerjoin(OrderItem, OrderItem.order_id == Order.id)
            .outerjoin(ItemFormData, ItemFormData.item_id == OrderItem.id)
            .filter(Order.version == version)
        )

        if value and value.strip():
            like_value = f"%{value.strip()}%"
            query = query.filter(
                or_(
                    Order.name.ilike(like_value),
                    Order.customer_name.ilike(like_value),
                    Order.phone.ilike(like_value),
                    ItemFormData.field_value.ilike(like_value),
                )
            )

        # ✅ 指定主键去重，更安全
        return query.distinct(Order.id)

    # ========= 序列化 =========
    @staticmethod
    def _mask_phone(phone: str) -> str | None:
        if not phone:
            return phone

        if len(phone) <= 4:
            return phone

        return "X" * (len(phone) - 4) + phone[-4:]
    
    @staticmethod
    def to_dict(order: Order) -> dict:
        session_phone = session.get("phone")
        is_login = bool(current_user and current_user.is_authenticated)
        is_owner = session_phone and session_phone == order.phone

        phone = order.phone if is_login or is_owner else OrderService._mask_phone(order.phone)

        data = {
            "id": order.id,
            "status": OrderService._get_payment_status(order),
            "name": order.name,
            "email": order.email,
            "customer_name": order.customer_name,
            "member_name": order.member_name,
            "phone": phone,
            "created_at": OrderService._format_created_at(order),
            "version": order.version,
            "login": is_login ,
            "owner": is_owner,
        }

        if is_login or is_owner:
            data["order_items"] = [
                OrderService._order_item_to_dict(item)
                for item in (order.order_items or [])
            ]

        return data


    @staticmethod
    def _order_item_to_dict(item: OrderItem, full: bool = False) -> dict:
        # 🧮 价格处理（full 模式下兼容 code == "D"）
        price_value = item.price
        if full and item.code == "D":
            for fd in item.item_form_data:
                if fd.field_name == "price":
                    price_value = fd.field_value
                    break

        try:
            price = int(float(price_value)) if price_value is not None else 0
        except (ValueError, TypeError):
            price = 0

        item_data = {
            "id": item.id,
            "order_id": item.order_id,
            "code": item.code,
            "item_name": item.item_name,
            "price": price,
        }

        if full:
            # 1️⃣ 结构化表单字段
            form_data_dict = {}
            for fd in item.item_form_data:
                key = fd.field_name
                val = {
                    "val": fd.field_value,
                    "val_id": fd.id
                }
                form_data_dict.setdefault(key, []).append(val)

            item_data["item_form_data"] = form_data_dict

            # 2️⃣ item_location 信息
            item_location = []
            for pdf_page in item.pdf_pages:
                pdf = pdf_page.print_pdf
                if not pdf:
                    continue

                location_entry = {
                    "print_pdf": pdf.to_dict(),
                    "pdf_page_data": pdf_page.to_dict(),
                    "boards": []
                }

                for board_data in pdf.boards:
                    board = board_data.board
                    if board:
                        location_entry["boards"].append({
                            "board_id": board.id,
                            "board_name": board.board_name
                        })

                item_location.append(location_entry)

            item_data["item_location"] = item_location

        else:
            # 🔹 简版表单结构
            item_data["item_form_data"] = [
                OrderService._item_form_data_to_dict(fd)
                for fd in (item.item_form_data or [])
            ]

        return item_data


    @staticmethod
    def _item_form_data_to_dict(data: ItemFormData) -> dict:
        return {
            "id": data.id,
            "item_id": data.item_id,
            "field_name": data.field_name,
            "field_value": data.field_value
        }

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

    @staticmethod
    def to_all_detail(order_id: int) -> dict | None:
        # ① 查订单
        order = Order.query.get(order_id)
        if not order:
            return None

        # ② 权限判断
        session_phone = session.get("phone")
        is_login = bool(current_user and current_user.is_authenticated)
        is_owner = session_phone and session_phone == order.phone

        if not is_login and not is_owner:
            return {
                "status": "error",
                "message": "未登录或没有权限查看此订单"
            }

        # ③ 基础信息（内部会自动判断 login & mask）
        order_data = OrderService.to_dict(order)

        # ④ 明细：直接用自己的内部函数
        order_data["order_items"] = [
            OrderService._order_item_to_dict(item, full=True)
            for item in order.order_items
        ]

        # ⑤ 前后订单 ID
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
    
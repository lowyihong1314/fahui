from datetime import datetime

from sqlalchemy import text

from app.extensions import db
from app.models import BoardData, BoardHeader, ItemFormData, Order, OrderItem, PDFPageData, PrintPDF
from app.services.board_service import BoardService


class BoardCommandService:
    PRICE_MAP = {
        "A1": 100,
        "A2": 100,
        "A3": 100,
        "B1": 35,
        "B2": 35,
        "B3": 35,
        "C": 15,
        "D1": 50,
    }

    @staticmethod
    def insert_pdf(data: dict):
        board_id = data.get("board_id")
        pdf_id = data.get("pdf_id")
        location = data.get("location")
        if not board_id or not pdf_id or not location:
            return {"error": "board_id, pdf_id, location 都不能为空"}, 400

        try:
            board_id = int(board_id)
            pdf_id = int(pdf_id)
            location = int(location)
        except ValueError:
            return {"error": "参数必须是整数"}, 400

        entry = BoardData.query.filter_by(print_pdf_id=pdf_id, board_id=board_id).first()
        if not entry:
            return {"error": f"pdf_id={pdf_id} 不存在于 board_id={board_id}"}, 400

        old_location = entry.location
        if old_location == location:
            return {"success": True, "message": "位置未改变"}, 200

        if old_location < location:
            BoardData.query.filter(
                BoardData.board_id == board_id,
                BoardData.location > old_location,
                BoardData.location <= location,
            ).update({BoardData.location: BoardData.location - 1}, synchronize_session=False)
        else:
            BoardData.query.filter(
                BoardData.board_id == board_id,
                BoardData.location >= location,
                BoardData.location < old_location,
            ).update({BoardData.location: BoardData.location + 1}, synchronize_session=False)

        entry.location = location
        db.session.commit()
        return {
            "success": True,
            "board_id": board_id,
            "pdf_id": pdf_id,
            "location": location,
            "all_board": BoardService.get_all_boards_with_orders(),
        }, 200

    @staticmethod
    def add_pdf(data: dict):
        board_id = data.get("board_id")
        pdf_id = data.get("pdf_id")
        board_name = data.get("board_name")

        def parse_int(val):
            if val in ["", None]:
                return None
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        board_width = parse_int(data.get("board_width"))
        board_height = parse_int(data.get("board_height"))

        if not board_id:
            return {"error": "board_id 不能为空"}, 400

        if pdf_id in ["none", "", None]:
            pdf_id = None
        else:
            try:
                pdf_id = int(pdf_id)
            except ValueError:
                return {"error": "pdf_id 必须是整数或 none"}, 400

        if pdf_id:
            pdf = PrintPDF.query.get(pdf_id)
            if not pdf:
                return {"error": f"print_pdf_id={pdf_id} 不存在"}, 400

            existing = BoardData.query.filter_by(print_pdf_id=pdf_id).first()
            if existing:
                return {"error": f"pdf_id={pdf_id} 已经绑定在 board_id={existing.board_id} 上"}, 400

        header = BoardHeader.query.get(board_id)
        if not header:
            header = BoardHeader(
                id=board_id,
                board_name=board_name or f"board_{board_id}",
                board_width=board_width,
                board_height=board_height,
            )
            db.session.add(header)
            db.session.flush()
        else:
            if board_width is not None:
                header.board_width = board_width
            if board_height is not None:
                header.board_height = board_height
            if board_name:
                header.board_name = board_name

        board_entry = None
        if pdf_id:
            board_entry = BoardData.query.filter_by(board_id=header.id, print_pdf_id=None).first()
            if board_entry:
                board_entry.print_pdf_id = pdf_id
            else:
                last_location = (
                    db.session.query(db.func.max(BoardData.location))
                    .filter_by(board_id=header.id)
                    .scalar()
                    or 0
                )
                board_entry = BoardData(
                    board_id=header.id,
                    print_pdf_id=pdf_id,
                    location=last_location + 1,
                )
                db.session.add(board_entry)

        db.session.commit()
        return {
            "side_id": board_entry.id if board_entry else None,
            "pdf_id": pdf_id,
            "pdf_data": [],
            "all_board": BoardService.get_all_boards_with_orders(),
        }, 200

    @staticmethod
    def clear_print_pdf():
        db.session.query(PDFPageData).delete()
        db.session.commit()
        db.session.query(PrintPDF).delete()
        db.session.commit()
        db.session.execute(text("ALTER TABLE pdf_page_data AUTO_INCREMENT = 1"))
        db.session.execute(text("ALTER TABLE print_pdf AUTO_INCREMENT = 1"))
        db.session.commit()
        return {"success": True, "message": "Tables cleared and IDs reset"}, 200

    @staticmethod
    def update_customer(order_id: int, data: dict, is_authenticated: bool):
        order = Order.query.get(order_id)
        if not order:
            return {"success": False, "message": "Order not found"}, 404

        order.customer_name = data.get("customer_name", order.customer_name)
        order.email = data.get("email", order.email)

        new_phone = data.get("phone")
        if new_phone and new_phone != order.phone:
            if is_authenticated:
                order.phone = new_phone
            else:
                return {"success": False, "message": "未登录用户无法修改手机号"}, 403

        db.session.commit()
        return {"success": True, "message": "Customer info updated"}, 200

    @classmethod
    def get_item_price(cls, code):
        return cls.PRICE_MAP.get(code, 0)

    @classmethod
    def add_paiwei(cls, order_id: int, data: dict):
        owner = data.get("owner")
        deceased = data.get("deceased")
        code = data.get("form-group")

        has_valid_owner = isinstance(owner, list) and any((name or "").strip() for name in owner)
        has_valid_deceased = (
            (isinstance(deceased, str) and deceased.strip())
            or (isinstance(deceased, list) and any((item or "").strip() for item in deceased))
        )

        if isinstance(owner, list):
            for name in owner:
                if name and len(name.strip()) > 50:
                    return {"success": False, "message": f"施主姓名“{name}”不能超过 5 个字"}, 400

        if code in ["A2", "B2"] and not (has_valid_owner and has_valid_deceased):
            return {"success": False, "message": "A2/B2 表单必须同时填写 owner 和 deceased"}, 400
        if code != "D1" and not (has_valid_owner or has_valid_deceased):
            return {"success": False, "message": "必须填写 owner 或 deceased 至少一项"}, 400

        order_item = OrderItem(
            order_id=order_id,
            code=code,
            item_name=data.get("item_name"),
            price=data.get("price") if data.get("price") is not None else cls.get_item_price(code),
        )
        db.session.add(order_item)
        db.session.commit()

        skip_keys = {"form_code", "form-group", "item_name", "price"}
        for key, value in data.items():
            if key in skip_keys:
                continue
            values = value if isinstance(value, list) else [value]
            for item in values:
                if item is None or str(item).strip() == "":
                    continue
                db.session.add(
                    ItemFormData(
                        item_id=order_item.id,
                        field_name=key,
                        field_value=str(item).strip(),
                    )
                )

        db.session.commit()
        return {"success": True, "message": "已保存", "item_id": order_item.id}, 200

    @staticmethod
    def delete_item(item_id: int):
        item = OrderItem.query.get(item_id)
        if not item:
            return {"success": False, "message": "未找到该订单项"}, 404

        ItemFormData.query.filter_by(item_id=item_id).delete()
        db.session.delete(item)
        db.session.commit()
        return {"success": True, "message": "删除成功"}, 200

    @staticmethod
    def delete_orders(data: dict):
        orders = data.get("data", [])
        if not orders:
            return {"status": "error", "message": "未提供任何订单数据"}, 400

        order_ids = [order["id"] for order in orders if "id" in order]
        if not order_ids:
            return {"status": "error", "message": "数据中没有包含订单 ID"}, 400

        orders_to_delete = Order.query.filter(Order.id.in_(order_ids)).all()
        deleted_count = 0
        marked_count = 0
        for order in orders_to_delete:
            if str(order.version) == "DELETE":
                db.session.delete(order)
                deleted_count += 1
            else:
                order.version = "DELETE"
                marked_count += 1

        db.session.commit()
        return {
            "status": "success",
            "message": f"标记删除 {marked_count} 个订单，物理删除 {deleted_count} 个订单",
            "marked": marked_count,
            "deleted": deleted_count,
        }, 200

    @staticmethod
    def copy_old_data(data: dict):
        order_id = data.get("order_id")
        new_version = "2025_YLP"
        if not order_id or new_version is None:
            return {"error": "order_id and new_version are required"}, 400

        old_order = Order.query.get(order_id)
        if not old_order:
            return {"error": f"Order with id {order_id} not found"}, 404
        if old_order.version == new_version:
            return {
                "error": f"Order {order_id} already has version {new_version}, cannot copy again.",
            }, 400

        new_order = Order(
            name=old_order.name,
            email=old_order.email,
            customer_name=old_order.customer_name,
            member_name=old_order.member_name,
            phone=old_order.phone,
            created_at=datetime.utcnow(),
            version=new_version,
        )
        db.session.add(new_order)
        db.session.flush()

        old_items = OrderItem.query.filter_by(order_id=old_order.id).all()
        for old_item in old_items:
            new_item = OrderItem(
                order_id=new_order.id,
                code=old_item.code,
                item_name=old_item.item_name,
                price=old_item.price,
            )
            db.session.add(new_item)
            db.session.flush()

            form_data_list = ItemFormData.query.filter_by(item_id=old_item.id).all()
            for old_data in form_data_list:
                db.session.add(
                    ItemFormData(
                        item_id=new_item.id,
                        field_name=old_data.field_name,
                        field_value=old_data.field_value,
                    )
                )

        db.session.commit()
        return {"message": "Order copied successfully", "new_order_id": new_order.id}, 201

    @staticmethod
    def update_item_form_value(data: dict):
        item_form_id = data.get("id")
        new_value = data.get("value")
        if not item_form_id or new_value is None:
            return {"success": False, "message": "缺少参数"}, 400

        item_form = ItemFormData.query.get(item_form_id)
        if not item_form:
            return {"success": False, "message": "未找到数据"}, 404

        item_form.field_value = new_value
        db.session.commit()
        return {"success": True}, 200

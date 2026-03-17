from sqlalchemy import func, or_

from app.extensions import db
from app.models import BoardData, ItemFormData, Order, OrderItem, PrintPDF
from app.services.board_service import BoardService
from app.services.order_service import OrderService


class BoardQueryService:
    @staticmethod
    def get_pdf_data(pdf_id: int):
        pdf = PrintPDF.query.get(pdf_id)
        if not pdf:
            return {"status": "error", "message": f"PrintPDF {pdf_id} 不存在"}, 404
        return {"status": "success", "data": pdf.to_dict()}, 200

    @staticmethod
    def delete_board(board_data_id: int):
        board = BoardData.query.get(board_data_id)
        if not board:
            return {
                "status": "error",
                "message": f"BoardData {board_data_id} not found",
            }, 404

        db.session.delete(board)
        db.session.commit()
        return {
            "status": "success",
            "message": f"BoardData {board_data_id} deleted successfully",
            "all_board": BoardService.get_all_boards_with_orders(),
        }, 200

    @staticmethod
    def list_all_boards():
        return {"all_board": BoardService.get_all_boards_with_orders()}

    @staticmethod
    def get_all_print_data():
        records = PrintPDF.query.order_by(PrintPDF.created_at.desc()).all()
        return [record.to_dict() for record in records]

    @staticmethod
    def get_version_list():
        versions = db.session.query(Order.version).distinct().all()
        return [version[0] for version in versions if version[0] is not None]

    @staticmethod
    def get_order_detail(order_id: int):
        if not order_id:
            return {"error": "Missing 'id' parameter"}, 400

        order = Order.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404

        return OrderService.to_all_detail(order_id), 200

    @staticmethod
    def check_duplicate_owner_fields():
        subquery = (
            db.session.query(
                ItemFormData.item_id,
                func.count(ItemFormData.id).label("owner_count"),
            )
            .filter(ItemFormData.field_name == "owner")
            .group_by(ItemFormData.item_id)
            .having(func.count(ItemFormData.id) > 1)
            .subquery()
        )
        order_ids = (
            db.session.query(OrderItem.order_id)
            .join(subquery, OrderItem.id == subquery.c.item_id)
            .distinct()
            .all()
        )
        return [order_id[0] for order_id in order_ids]

    @staticmethod
    def search_orders(keyword: str, is_authenticated: bool):
        keyword = (keyword or "").strip().lower()
        if not keyword:
            return {"success": True, "results": []}

        orders = []
        if keyword.isdigit():
            order = Order.query.filter_by(id=int(keyword)).first()
            if order:
                orders = [order]

            if not orders:
                order_item = OrderItem.query.filter_by(id=int(keyword)).first()
                if order_item:
                    orders = [order_item.order]

            if not orders:
                orders = (
                    Order.query.filter(Order.phone.like(f"%{keyword}%"))
                    .order_by(Order.created_at.desc())
                    .limit(5)
                    .all()
                )
        else:
            orders = (
                Order.query.filter(
                    or_(
                        Order.customer_name.ilike(f"%{keyword}%"),
                        Order.name.ilike(f"%{keyword}%"),
                        Order.member_name.ilike(f"%{keyword}%"),
                    )
                )
                .order_by(Order.created_at.desc())
                .limit(5)
                .all()
            )

        if not orders:
            matched_item_ids = (
                db.session.query(ItemFormData.item_id)
                .filter(ItemFormData.field_value.ilike(f"%{keyword}%"))
                .limit(10)
                .all()
            )
            item_ids = [item_id for (item_id,) in matched_item_ids]
            if item_ids:
                order_ids = (
                    db.session.query(OrderItem.order_id)
                    .filter(OrderItem.id.in_(item_ids))
                    .limit(10)
                    .all()
                )
                flat_order_ids = [order_id for (order_id,) in order_ids]
                if flat_order_ids:
                    top_ids = sorted(flat_order_ids, reverse=True)[:5]
                    orders = Order.query.filter(Order.id.in_(top_ids)).all()
                    orders.sort(key=lambda order: top_ids.index(order.id))

        results = []
        for order in orders:
            if order.version == "DELETE" and not is_authenticated:
                continue
            results.append(OrderService.to_dict(order))
        return {"success": True, "results": results}

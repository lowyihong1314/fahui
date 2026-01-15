# services/board_service.py

from sqlalchemy.orm import joinedload
from app.extensions import db
from models.fahui import BoardHeader, BoardData


class BoardService:
    # ========= 单一查询 =========

    @staticmethod
    def get_pdf_location(pdf_id: int):
        board_data = (
            BoardData.query
            .options(joinedload(BoardData.board))
            .filter_by(print_pdf_id=pdf_id)
            .first()
        )

        if not board_data:
            return None

        board = board_data.board
        total_on_board = len(board.board_data)

        return {
            "board_id": board.id,
            "board_name": board.board_name,
            "total_on_board": total_on_board,
            "pdf_location": board_data.location
        }

    # ========= 汇总查询 =========

    @staticmethod
    def get_all_boards_with_orders():

        headers = db.session.query(BoardHeader).all()
        result = []

        for header in headers:
            grouped = []

            for b in header.board_data:
                order_seen = set()
                order_list = []

                pdf = b.print_pdf
                if pdf:
                    for pd in pdf.page_data:
                        if not (pd.order_item and pd.order_item.order):
                            continue

                        order = pd.order_item.order
                        if order.id in order_seen:
                            continue

                        order_seen.add(order.id)

                        owner_or_deceased = None
                        form_data = pd.order_item.item_form_data or []

                        # 优先 owner
                        for fd in form_data:
                            if fd.field_name == "owner":
                                owner_or_deceased = fd.field_value
                                break

                        # fallback deceased
                        if not owner_or_deceased:
                            for fd in form_data:
                                if fd.field_name == "deceased":
                                    owner_or_deceased = fd.field_value
                                    break

                        order_list.append({
                            "order_item_id": pd.order_item.id,
                            "order_id": order.id,
                            "customer_name": order.customer_name,
                            "owner_or_deceased": owner_or_deceased
                        })

                grouped.append({
                    "width": pdf.width if pdf else None,
                    "height": pdf.height if pdf else None,
                    "print_pdf_id": b.print_pdf_id,
                    "side_id": b.id,
                    "location": b.location,
                    "orders": order_list
                })

            result.append({
                "board_id": header.id,
                "board_name": header.board_name,
                "board_width": header.board_width,
                "board_height": header.board_height,
                "board_data": grouped
            })

        return result

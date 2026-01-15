# services/order_item_service.py

from models.fahui import OrderItem


class OrderItemService:
    """OrderItem 相关业务逻辑"""

    # ========= 基础工具 =========

    @staticmethod
    def _calc_price(item: OrderItem) -> int:
        """
        价格计算逻辑
        - 默认使用 item.price
        - code == 'D' 时，从 ItemFormData 中找 price
        - 最终强制转 int
        """
        price_value = item.price

        if item.code == "D":
            for fd in item.item_form_data:
                if fd.field_name == "price":
                    price_value = fd.field_value
                    break

        try:
            return int(float(price_value)) if price_value is not None else 0
        except (ValueError, TypeError):
            return 0

    # ========= 对外方法 =========

    @staticmethod
    def get_board_data(order_item_id: int):
        """
        原 OrderItem.get_board_data
        """
        order_item = OrderItem.query.get(order_item_id)
        if not order_item:
            return None

        board_data_list = []

        for pdf_page in order_item.pdf_pages:
            # ⚠️ 你当前结构里 board_data 是通过 print_pdf 关联的
            pdf = pdf_page.print_pdf
            if not pdf:
                continue

            for b_data in pdf.boards:
                board = b_data.board
                if not board:
                    continue

                board_data_list.append({
                    "board_data_id": b_data.id,
                    "board_id": board.id,
                    "board_name": board.board_name,
                    "board_width": board.board_width,
                    "location": b_data.location
                })

        return board_data_list or None

    @staticmethod
    def to_dict(item: OrderItem) -> dict:
        """
        原 OrderItem.to_dict
        """
        return {
            "id": item.id,
            "order_id": item.order_id,
            "code": item.code,
            "item_name": item.item_name,
            "price": OrderItemService._calc_price(item)
        }

    @staticmethod
    def to_all_print(item: OrderItem) -> dict:
        """
        原 OrderItem.to_all_print
        """
        item_data = OrderItemService.to_dict(item)

        form_data_dict = {}
        for fd in item.item_form_data:
            key = fd.field_name
            val = fd.field_value

            if key in form_data_dict:
                if isinstance(form_data_dict[key], list):
                    form_data_dict[key].append(val)
                else:
                    form_data_dict[key] = [form_data_dict[key], val]
            else:
                form_data_dict[key] = val

        item_data["item_form_data"] = form_data_dict
        return item_data

    @staticmethod
    def to_all_detail(item: OrderItem) -> dict:
        """
        原 OrderItem.to_all_detail
        """
        item_data = OrderItemService.to_dict(item)

        # 1️⃣ ItemFormData 结构化
        form_data_dict = {}
        for fd in item.item_form_data:
            key = fd.field_name
            val = {
                "val": fd.field_value,
                "val_id": fd.id
            }
            form_data_dict.setdefault(key, []).append(val)

        item_data["item_form_data"] = form_data_dict

        # 2️⃣ item_location
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

        return item_data

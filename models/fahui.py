from models import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Time, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import event,inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from flask_login import current_user
from models.user_data import User
from collections import defaultdict
from sqlalchemy import func

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自动递增的主键
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    member_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    version = db.Column(db.Integer, nullable=False) 
    payments = db.relationship('PaymentData', back_populates='order', cascade='all, delete-orphan')

    # 反向关系，表明每个订单可以有多个 OrderItem
    order_items = relationship(
        'OrderItem',
        back_populates='order',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f"<Order(id={self.id}, status={self.status}, customer_name={self.customer_name}, created_at={self.created_at}, version={self.version})>"

    # to_dict: 获取普通订单信息
    def to_dict(self):
        # 如果是 DELETE 版本并且用户未登录，直接返回 None
 
        created_at_str = self.created_at.strftime('%y-%m-%d_%H:%M') if self.created_at else None

        # 从关联的 payments 获取最新状态
        latest_payment = None
        if self.payments:
            latest_payment = max(self.payments, key=lambda p: p.created_at)

        payment_status = latest_payment.status if latest_payment else "Not-ready"

        return {
            "id": self.id,
            "status": payment_status,
            "name": self.name,
            "email": self.email,
            "customer_name": self.customer_name,
            "member_name": self.member_name,
            "phone": self.phone,
            "created_at": created_at_str,
            "version": self.version,
            "login": True if current_user and current_user.is_authenticated else False
        }

    # to_all_detail: 获取详细订单信息，包括 OrderItem 和 ItemFormData
    def to_all_detail(self):
        order_data = self.to_dict()
        order_data["order_items"] = [item.to_all_detail() for item in self.order_items]

        # 查询前一条和后一条订单（按 ID）
        prev_order = Order.query.filter(Order.id < self.id).order_by(Order.id.desc()).first()
        next_order = Order.query.filter(Order.id > self.id).order_by(Order.id.asc()).first()

        order_data["prev_id"] = prev_order.id if prev_order else None
        order_data["next_id"] = next_order.id if next_order else None

        return order_data

    @staticmethod
    def get_order_data_by_version(version):
        # 根据 version 查询订单
        orders = Order.query.filter_by(version=version).all()
        
        # 将每个订单转换为字典并返回
        return [order.to_dict() for order in orders]
    
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete="CASCADE"),
        nullable=False
    )

    code = db.Column(db.String(20), nullable=True)
    item_name = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=True)  # 使用 db.Float 代替 Decimal
    
    order = relationship('Order', back_populates='order_items')
    pdf_pages = db.relationship('PDFPageData', back_populates='order_item', cascade='all, delete-orphan')

    # 反向关系，表示 OrderItem 属于一个 Order
    item_form_data = relationship(
        'ItemFormData',
        back_populates='item',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, item_name={self.item_name}, price={self.price})>"
    
    @classmethod
    def get_board_data(cls, order_item_id: int):
        # Step 1: 查找对应的 OrderItem
        order_item = cls.query.get(order_item_id)
        if not order_item:
            return None
        
        # Step 2: 查找对应的 PDFPageData
        # 假设 OrderItem 和 PDFPageData 通过关系关联，直接获取相关数据
        pdf_pages = order_item.pdf_pages  # 获取该订单项的所有 PDF 页数据
        
        board_data_list = []
        for pdf_page in pdf_pages:
            # Step 3: 查找 BoardData
            board_data = pdf_page.board_data  # 假设通过 pdf_page 直接能获取到 board_data
            if board_data:
                for b_data in board_data:
                    board_header = b_data.board  # 获取 BoardHeader
                    board_data_list.append({
                        "board_data_id": b_data.id,
                        "board_name": board_header.board_name,
                        "board_width": board_header.board_width,  # 加入 board_width
                        "board_id": board_header.id,
                        "location": b_data.location
                    })

        return board_data_list if board_data_list else None
    
    # to_dict: 获取普通订单项信息
    def to_dict(self):
        price_value = self.price

        # 特殊逻辑：如果 code == "D"，优先从 ItemFormData 里取 price
        if self.code == "D":
            for fd in self.item_form_data:
                if fd.field_name == "price":
                    price_value = fd.field_value
                    break

        # 强制转成 int（失败就置为 0）
        try:
            price_value = int(float(price_value)) if price_value is not None else 0
        except (ValueError, TypeError):
            price_value = 0

        return {
            "id": self.id,
            "order_id": self.order_id,
            "code": self.code,
            "item_name": self.item_name,
            "price": price_value
        }
    # to_all_detail: 获取详细订单项信息，包括 ItemFormData
    def to_all_print(self):
        item_data = self.to_dict()

        form_data_dict = {}
        for fd in self.item_form_data:
            key = fd.field_name
            val = fd.field_value
            if key in form_data_dict:
                # 已有同名字段，转成列表或追加
                if isinstance(form_data_dict[key], list):
                    form_data_dict[key].append(val)
                else:
                    form_data_dict[key] = [form_data_dict[key], val]
            else:
                form_data_dict[key] = val

        item_data["item_form_data"] = form_data_dict
        return item_data
    
    def to_all_detail(self):
        item_data = self.to_dict()

        # ✅ 1. 转换 item_form_data 为字典结构
        form_data_dict = {}
        for fd in self.item_form_data:
            key = fd.field_name
            val = {"val": fd.field_value, "val_id": fd.id}
            form_data_dict.setdefault(key, []).append(val)

        item_data["item_form_data"] = form_data_dict

        # ✅ 2. 构建 item_location
        item_location = []

        for pdf_page in self.pdf_pages:
            pdf_info = pdf_page.print_pdf
            if not pdf_info:
                continue

            location_entry = {
                "print_pdf": pdf_info.to_dict(),
                "pdf_page_data": pdf_page.to_dict(),
                "boards": []
            }

            for board_data in pdf_info.boards:
                if board_data.board:
                    location_entry["boards"].append({
                        "board_id": board_data.board.id,
                        "board_name": board_data.board.board_name
                    })

            item_location.append(location_entry)

        item_data["item_location"] = item_location

        return item_data

class BoardHeader(db.Model):
    __tablename__ = 'board_header'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    board_name = db.Column(db.String(255), nullable=False)
    board_width = db.Column(db.Integer, nullable=True)  
    board_height = db.Column(db.Integer, nullable=True)

    # 🔗 反向关系：header -> data
    board_data = db.relationship(
        "BoardData",
        back_populates="board",
        order_by="BoardData.created_at"   # ✅ 按创建时间排序
    )
    @classmethod
    def get_pdf_location(cls, pdf_id: int):
        """返回指定 pdf_id 在哪个 board 里的位置，以及 board 的信息"""
        from sqlalchemy.orm import joinedload

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
            "pdf_location": board_data.location  # ✅ 直接用数据库字段
        }

    @classmethod
    def to_all(cls):
        """返回所有 BoardHeader 及其关联的 BoardData/PrintPDF/Orders"""
        headers = db.session.query(cls).all()
        result = []

        for header in headers:
            grouped = []
            for b in header.board_data:
                order_seen = set()
                order_list = []

                if b.print_pdf:
                    for pd in b.print_pdf.page_data:
                        if pd.order_item and pd.order_item.order:
                            order = pd.order_item.order
                            if order.id not in order_seen:
                                order_seen.add(order.id)

                                owner_or_deceased = None
                                if pd.order_item.item_form_data:
                                    # 优先 owner，再 deceased
                                    for fd in pd.order_item.item_form_data:
                                        if fd.field_name == "owner":
                                            owner_or_deceased = fd.field_value
                                            break
                                    if not owner_or_deceased:
                                        for fd in pd.order_item.item_form_data:
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
                    "width": b.print_pdf.width if b.print_pdf else None,
                    "height": b.print_pdf.height if b.print_pdf else None,
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

class BoardData(db.Model):
    __tablename__ = 'board_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    board_id = db.Column(db.Integer, db.ForeignKey('board_header.id'), nullable=False, index=True)
    print_pdf_id = db.Column(db.Integer, db.ForeignKey('print_pdf.id'), nullable=True)

    print_pdf = db.relationship('PrintPDF', backref=db.backref('boards', lazy=True))
    board = db.relationship('BoardHeader', back_populates='board_data')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ✅ 新字段：记录该 pdf 在 board 内的序号
    location = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<BoardData(id={self.id}, board_id={self.board_id}, location={self.location})>"

    def to_dict(self):
        return {
            "id": self.id,
            "board_id": self.board_id,
            "print_pdf_id": self.print_pdf_id,
            "location": self.location,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }


class PrintPDF(db.Model):
    __tablename__ = 'print_pdf'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 直接当 page_id 用
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ✅ 新增字段：宽高
    width = db.Column(db.Integer, nullable=True)   # PDF 宽度
    height = db.Column(db.Integer, nullable=True)  # PDF 高度

    # ✅ 一对多关系
    page_data = db.relationship('PDFPageData', back_populates='print_pdf', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<PrintPDF(id={self.id}, created_at={self.created_at}, width={self.width}, height={self.height})>"

    def to_dict(self):
        return {
            "id": self.id,  # 本身就是 page_id
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            "width": self.width,
            "height": self.height,
            "page_data": [pd.to_dict() for pd in self.page_data]
        }

class PDFPageData(db.Model):
    __tablename__ = 'pdf_page_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    print_pdf_id = db.Column(db.Integer, db.ForeignKey('print_pdf.id', ondelete="CASCADE"), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id', ondelete="CASCADE"), nullable=False)

    # ✅ 正确的关系：属于哪个 PrintPDF
    print_pdf = db.relationship('PrintPDF', back_populates='page_data')

    # 关系：对应的 OrderItem
    order_item = db.relationship('OrderItem', back_populates='pdf_pages')

    def __repr__(self):
        return f"<PDFPageData(id={self.id}, print_pdf_id={self.print_pdf_id}, order_item_id={self.order_item_id})>"

    def to_dict(self, with_order_item=False):
        """转成 dict，可选是否包含 order_item 的详细信息"""
        data = {
            "id": self.id,
            "print_pdf_id": self.print_pdf_id,
            "order_item_id": self.order_item_id,
            "order_id": self.order_item.order_id if self.order_item else None
        }
        return data


class ItemFormData(db.Model):
    __tablename__ = 'item_form_data'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey('order_items.id', ondelete="CASCADE"),
        nullable=True
    )

    field_name = db.Column(db.String(100), nullable=True)
    field_value = db.Column(db.Text, nullable=True)  # 使用 db.Text 代替 Text 类型

    # 反向关系，表示每个 ItemFormData 属于一个 OrderItem
    item = relationship('OrderItem', back_populates='item_form_data')

    def __repr__(self):
        return f"<ItemFormData(id={self.id}, item_id={self.item_id}, field_name={self.field_name}, field_value={self.field_value})>"

    # to_dict: 获取 ItemFormData 信息
    def to_dict(self):
        return {
            "id": self.id,
            "item_id": self.item_id,
            "field_name": self.field_name,
            "field_value": self.field_value
        }
    
# === Order 表保护 ===
@event.listens_for(Order, 'before_update', propagate=True)
def prevent_order_update(mapper, connection, target):
    if target.version == '2024_YLP':
        state = inspect(target)
        changed = {attr.key for attr in state.attrs if attr.history.has_changes()}

        # 只允许 phone 更新
        if changed != {"phone"}:
            raise ValueError("Order with version '2024_YLP' is read-only (except phone).")

@event.listens_for(Order, 'before_delete', propagate=True)
def prevent_order_delete(mapper, connection, target):
    if target.version == '2024_YLP':
        raise ValueError("Order with version '2024_YLP' is read-only and cannot be deleted.")

# === OrderItem 表保护 ===
@event.listens_for(OrderItem, 'before_update', propagate=True)
def prevent_order_item_update(mapper, connection, target):
    if target.order and target.order.version == '2024_YLP':
        raise ValueError("Cannot update OrderItem: parent Order is read-only (version '2024_YLP').")

@event.listens_for(OrderItem, 'before_delete', propagate=True)
def prevent_order_item_delete(mapper, connection, target):
    if target.order and target.order.version == '2024_YLP':
        raise ValueError("Cannot delete OrderItem: parent Order is read-only (version '2024_YLP').")

# === ItemFormData 表保护 ===
@event.listens_for(ItemFormData, 'before_update', propagate=True)
def prevent_item_form_data_update(mapper, connection, target):
    if target.item and target.item.order and target.item.order.version == '2024_YLP':
        raise ValueError("Cannot update ItemFormData: parent Order is read-only (version '2024_YLP').")

@event.listens_for(ItemFormData, 'before_delete', propagate=True)
def prevent_item_form_data_delete(mapper, connection, target):
    if target.item and target.item.order and target.item.order.version == '2024_YLP':
        raise ValueError("Cannot delete ItemFormData: parent Order is read-only (version '2024_YLP').")
    
@event.listens_for(OrderItem, 'before_insert', propagate=True)
def prevent_order_item_insert(mapper, connection, target):
    if target.order and target.order.version == '2024_YLP':
        raise ValueError("Cannot add OrderItem: parent Order is read-only (version '2024_YLP').")
    elif target.order_id:
        order = db.session.query(Order).get(target.order_id)
        if order and order.version == '2024_YLP':
            raise ValueError("Cannot add OrderItem: parent Order is read-only (version '2024_YLP').")

@event.listens_for(ItemFormData, 'before_insert', propagate=True)
def prevent_item_form_data_insert(mapper, connection, target):
    if target.item and target.item.order and target.item.order.version == '2024_YLP':
        raise ValueError("Cannot add ItemFormData: parent Order is read-only (version '2024_YLP').")
    elif target.item_id:
        item = db.session.query(OrderItem).get(target.item_id)
        if item and item.order and item.order.version == '2024_YLP':
            raise ValueError("Cannot add ItemFormData: parent Order is read-only (version '2024_YLP').")

from app.extensions import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import event,inspect

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

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey('orders.id', ondelete="CASCADE"),
        nullable=False
    )

    code = db.Column(db.String(20))
    item_name = db.Column(db.String(100))
    price = db.Column(db.Float)

    order = relationship('Order', back_populates='order_items')
    pdf_pages = db.relationship('PDFPageData', back_populates='order_item', cascade='all, delete-orphan')
    item_form_data = relationship(
        'ItemFormData',
        back_populates='item',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f"<OrderItem id={self.id} order_id={self.order_id}>"


class BoardHeader(db.Model):
    __tablename__ = 'board_header'

    id = db.Column(db.Integer, primary_key=True)
    board_name = db.Column(db.String(255), nullable=False)
    board_width = db.Column(db.Integer)
    board_height = db.Column(db.Integer)

    board_data = db.relationship(
        "BoardData",
        back_populates="board",
        order_by="BoardData.created_at"
    )

    def __repr__(self):
        return f"<BoardHeader id={self.id} name={self.board_name}>"


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
    

def is_order_read_only(order) -> bool:
    from function.config import READ_ONLY_ORDER_VERSIONS

    return order and order.version in READ_ONLY_ORDER_VERSIONS

@event.listens_for(Order, "before_update", propagate=True)
def protect_order_update(mapper, connection, target):
    if not is_order_read_only(target):
        return

    state = inspect(target)
    changed = {attr.key for attr in state.attrs if attr.history.has_changes()}

    # 只允许改 phone
    if changed != {"phone"}:
        raise ValueError(
            f"Order version '{target.version}' is read-only (except phone)."
        )


@event.listens_for(Order, "before_delete", propagate=True)
def protect_order_delete(mapper, connection, target):
    if is_order_read_only(target):
        raise ValueError(
            f"Order version '{target.version}' is read-only and cannot be deleted."
        )

def get_parent_order_from_item(item):
    if item.order:
        return item.order
    if item.order_id:
        return db.session.get(Order, item.order_id)
    return None


@event.listens_for(OrderItem, "before_insert", propagate=True)
@event.listens_for(OrderItem, "before_update", propagate=True)
@event.listens_for(OrderItem, "before_delete", propagate=True)
def protect_order_item(mapper, connection, target):
    order = get_parent_order_from_item(target)
    if is_order_read_only(order):
        raise ValueError(
            f"Cannot modify OrderItem: parent Order version '{order.version}' is read-only."
        )

def get_parent_order_from_form_data(form_data):
    if form_data.item and form_data.item.order:
        return form_data.item.order
    if form_data.item_id:
        item = db.session.get(OrderItem, form_data.item_id)
        return item.order if item else None
    return None


@event.listens_for(ItemFormData, "before_insert", propagate=True)
@event.listens_for(ItemFormData, "before_update", propagate=True)
@event.listens_for(ItemFormData, "before_delete", propagate=True)
def protect_item_form_data(mapper, connection, target):
    order = get_parent_order_from_form_data(target)
    if is_order_read_only(order):
        raise ValueError(
            f"Cannot modify ItemFormData: parent Order version '{order.version}' is read-only."
        )

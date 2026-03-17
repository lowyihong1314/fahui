from datetime import datetime

from sqlalchemy.orm import relationship

from app.extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    member_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    version = db.Column(db.String(50), nullable=False)
    payments = db.relationship(
        "PaymentData",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    order_items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return (
            f"<Order(id={self.id}, customer_name={self.customer_name}, "
            f"created_at={self.created_at}, version={self.version})>"
        )


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    code = db.Column(db.String(20))
    item_name = db.Column(db.String(100))
    price = db.Column(db.Float)

    order = relationship("Order", back_populates="order_items")
    pdf_pages = db.relationship(
        "PDFPageData",
        back_populates="order_item",
        cascade="all, delete-orphan",
    )
    item_form_data = relationship(
        "ItemFormData",
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<OrderItem id={self.id} order_id={self.order_id}>"


class ItemFormData(db.Model):
    __tablename__ = "item_form_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(
        db.Integer,
        db.ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=True,
    )
    field_name = db.Column(db.String(100), nullable=True)
    field_value = db.Column(db.Text, nullable=True)

    item = relationship("OrderItem", back_populates="item_form_data")

    def __repr__(self):
        return (
            f"<ItemFormData(id={self.id}, item_id={self.item_id}, "
            f"field_name={self.field_name}, field_value={self.field_value})>"
        )

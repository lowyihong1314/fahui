from datetime import datetime

from app.extensions import db


class PrintPDF(db.Model):
    __tablename__ = "print_pdf"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    page_data = db.relationship(
        "PDFPageData",
        back_populates="print_pdf",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<PrintPDF(id={self.id}, created_at={self.created_at}, "
            f"width={self.width}, height={self.height})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.created_at
                else None
            ),
            "width": self.width,
            "height": self.height,
            "page_data": [page_data.to_dict() for page_data in self.page_data],
        }


class PDFPageData(db.Model):
    __tablename__ = "pdf_page_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    print_pdf_id = db.Column(
        db.Integer,
        db.ForeignKey("print_pdf.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_item_id = db.Column(
        db.Integer,
        db.ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
    )

    print_pdf = db.relationship("PrintPDF", back_populates="page_data")
    order_item = db.relationship("OrderItem", back_populates="pdf_pages")

    def __repr__(self):
        return (
            f"<PDFPageData(id={self.id}, print_pdf_id={self.print_pdf_id}, "
            f"order_item_id={self.order_item_id})>"
        )

    def to_dict(self, with_order_item=False):
        return {
            "id": self.id,
            "print_pdf_id": self.print_pdf_id,
            "order_item_id": self.order_item_id,
            "order_id": self.order_item.order_id if self.order_item else None,
        }

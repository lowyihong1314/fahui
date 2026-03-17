from datetime import datetime

from app.extensions import db


class BoardHeader(db.Model):
    __tablename__ = "board_header"

    id = db.Column(db.Integer, primary_key=True)
    board_name = db.Column(db.String(255), nullable=False)
    board_width = db.Column(db.Integer)
    board_height = db.Column(db.Integer)
    board_data = db.relationship(
        "BoardData",
        back_populates="board",
        order_by="BoardData.created_at",
    )

    def __repr__(self):
        return f"<BoardHeader id={self.id} name={self.board_name}>"


class BoardData(db.Model):
    __tablename__ = "board_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    board_id = db.Column(
        db.Integer,
        db.ForeignKey("board_header.id"),
        nullable=False,
        index=True,
    )
    print_pdf_id = db.Column(db.Integer, db.ForeignKey("print_pdf.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    location = db.Column(db.Integer, nullable=True)

    print_pdf = db.relationship("PrintPDF", backref=db.backref("boards", lazy=True))
    board = db.relationship("BoardHeader", back_populates="board_data")

    def __repr__(self):
        return (
            f"<BoardData(id={self.id}, board_id={self.board_id}, "
            f"location={self.location})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "board_id": self.board_id,
            "print_pdf_id": self.print_pdf_id,
            "location": self.location,
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if self.created_at
                else None
            ),
        }

import os
from io import BytesIO

from flask import jsonify, make_response
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy import func

from app.extensions import db
from app.function.common import data_path
from app.function.payment.service import get_label_cn_filter
from app.models import Order, OrderItem
from app.services.order_service import OrderService


def build_quotation_response(order_id: int):
    total_amount = (
        db.session.query(func.sum(OrderItem.price))
        .filter(OrderItem.order_id == order_id)
        .scalar()
    )
    total_amount = total_amount or 0

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order_detail = OrderService.to_all_detail(order_id)

    font_path = os.path.join(data_path, "kai.ttf")
    pdfmetrics.registerFont(TTFont("TW-Kai", font_path))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    logo_path = os.path.join(data_path, "logo/logo.png")
    try:
        logo = ImageReader(logo_path)
        logo_size = 60
        c.drawImage(
            logo,
            50,
            height - logo_size - 20,
            width=logo_size,
            height=logo_size,
            mask="auto",
        )
    except Exception as e:
        print(f"Failed to load logo image: {e}")

    c.setFont("TW-Kai", 28)
    c.drawString(120, height - 55, "地南佛学会")

    y = height - 100
    c.setFont("TW-Kai", 16)
    y -= 30

    c.setFont("TW-Kai", 12)
    c.drawString(50, y, f"功德主: {order_detail['customer_name']}")
    y -= 20
    c.drawString(50, y, f"联系电话: {order_detail['phone']}")
    y -= 20
    c.drawString(50, y, f"订单编号: {order_detail['id']}")
    y -= 20
    c.drawString(50, y, f"创建日期: {order_detail['created_at']}")
    y -= 60

    title_box_height = 40
    c.setFillColorRGB(0.9, 0.9, 0.95)
    c.rect(45, y - title_box_height + 10, width - 90, title_box_height, fill=1, stroke=0)
    c.setFillColor(colors.black)

    y -= 10
    c.setFont("TW-Kai", 14)
    c.drawString(50, y, "订单项目")
    y -= 30

    c.setFont("TW-Kai", 12)
    c.setLineWidth(1)
    c.setStrokeColor(colors.grey)
    c.drawString(50, y, "项目名称")
    c.drawString(250, y, "德金 (RM)")
    c.drawString(350, y, "相关信息")
    y -= 5
    c.line(45, y, width - 45, y)
    y -= 15

    c.setFont("TW-Kai", 12)
    for item in order_detail["order_items"]:
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("TW-Kai", 12)

        c.drawString(50, y, item["item_name"])
        c.drawString(250, y, f"{item['price']:.0f}")

        y_related = y
        for key, val_list in item["item_form_data"].items():
            if key == "price":
                continue
            vals = ", ".join(v["val"] for v in val_list)
            c.drawString(350, y_related, f"{get_label_cn_filter(key)}: {vals}")
            y_related -= 15
        y = y_related - 10

    if y < 50:
        c.showPage()
        y = height - 50
        c.setFont("TW-Kai", 12)

    c.setFont("TW-Kai", 14)
    c.drawString(50, y, f"总德金 (RM): {total_amount:.0f}")

    c.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=order_{order_id}_quotation.pdf"
    )
    return response

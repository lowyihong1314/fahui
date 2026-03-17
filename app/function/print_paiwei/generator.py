import io
import os
import re
import zipfile
from io import BytesIO

import qrcode
from flask import jsonify, send_file
from pdfrw import PageMerge, PdfReader, PdfWriter
from reportlab.graphics.barcode import code128
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.extensions import db
from app.function.common import data_path
from app.function.print_paiwei.points import (
    get_deceased_point,
    get_owner_point,
    get_point_data,
)
from app.models import Order, OrderItem, PDFPageData, PrintPDF
from app.services.order_item_service import OrderItemService


def filter_fahui_data(items):
    items_sorted = sorted(items, key=lambda item: item.id)
    fahui_data = [OrderItemService.to_all_print(item) for item in items_sorted]
    return [item for item in fahui_data if not str(item.get("code", "")).startswith("D")]


def generate_paiwei_using_order_item_ids(order_item_ids, need_barcode=False):
    items = OrderItem.query.filter(OrderItem.id.in_(order_item_ids)).all()
    if not items:
        return None

    filtered_data = filter_fahui_data(items)
    if not filtered_data:
        return None

    from PyPDF2 import PdfMerger

    grouped_data = {}
    for item in filtered_data:
        grouped_data.setdefault(item.get("code"), []).append(item)

    merger = PdfMerger()
    for code, grouped_items in grouped_data.items():
        point_data, source_name = get_point_data(code)
        if not point_data:
            continue

        buffer = generate_paiwei(
            code,
            grouped_items,
            point_data,
            source_name,
            need_barcode=need_barcode,
        )
        buffer.seek(0)
        merger.append(buffer)

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return output


def generate_paiwei_using_order_ids(order_ids, need_barcode=False):
    items = OrderItem.query.join(Order).filter(Order.id.in_(order_ids)).all()
    if not items:
        return jsonify({"status": "error", "message": "没有找到对应的订单数据"}), 400

    filtered_data = filter_fahui_data(items)
    if not filtered_data:
        return jsonify({"status": "error", "message": "没有有效的法会数据"}), 400

    grouped_data = {}
    for item in filtered_data:
        grouped_data.setdefault(item.get("code"), []).append(item)

    buffers = []
    for code, grouped_items in grouped_data.items():
        point_data, source_name = get_point_data(code)
        if not point_data:
            return jsonify({"status": "error", "message": f"⚠️ 找不到 point_data 对应 code: {code}"}), 400

        buffer = generate_paiwei(
            code,
            grouped_items,
            point_data,
            source_name,
            need_barcode=need_barcode,
        )
        buffers.append((code, buffer))

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for code, buffer in buffers:
            zipf.writestr(f"paiwei_{code}.pdf", buffer.getvalue())

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="paiwei_files.zip",
    )


def generate_paiwei(paiwei_type, fahui_data, point_data, source_name, need_barcode=False):
    if paiwei_type in ["A3", "B3"]:
        for item in fahui_data:
            form_data = item.get("item_form_data", {})
            owner_list = []
            if "mother" in form_data:
                val = form_data.pop("mother")
                owner_list.extend([f"母 {v}" for v in val] if isinstance(val, list) else [f"母 {val}"])
            if "father" in form_data:
                val = form_data.pop("father")
                owner_list.extend([f"父 {v}" for v in val] if isinstance(val, list) else [f"父 {val}"])
            if owner_list:
                form_data["owner"] = owner_list
            item["item_form_data"] = form_data

    output_path = os.path.join(data_path, "paiwei_result")
    os.makedirs(output_path, exist_ok=True)

    file_name = f"{source_name}.pdf"
    bg_pdf_path = os.path.join(data_path, "paiwei_template", file_name)
    font_path = os.path.join(data_path, "kai.ttf")
    pdfmetrics.registerFont(TTFont("TW-Kai", font_path))

    if source_name == "paiwei_5":
        page_size = landscape(A4)
        owner_point = get_owner_point("owner_point_B")
        deceased_point = get_deceased_point("deceased_point_B")
    elif source_name == "paiwei_1":
        page_size = A4
        owner_point = get_owner_point("owner_point_A")
        deceased_point = get_deceased_point("deceased_point_A")
    else:
        page_size = A4
        owner_point = get_owner_point("owner_point_C")
        deceased_point = get_deceased_point("deceased_point_C")

    temp_pdf_path = os.path.join(output_path, f"{source_name}_temp_text_{paiwei_type}.pdf")
    c = canvas.Canvas(temp_pdf_path, pagesize=page_size)
    width, height = page_size

    point_dict = {}
    for block in point_data:
        point_dict.update(block)

    def get_point(block_key, key):
        for pt in point_dict.get(block_key, []):
            if f"{key}_point" in pt:
                return pt[f"{key}_point"]
        return None

    positions = sorted(point_dict.keys())

    def draw_text_vertical(block_key, key, text, base_x, base_y, info):
        pt = get_point(block_key, key)
        if not pt:
            return

        dx, dy, size, spacing = pt
        x_base, y_base = base_x + dx, base_y + dy
        c.setFont("TW-Kai", size)

        if key == "owner":
            people = text if isinstance(text, list) else re.split(r"[,\\s]+", str(text).strip())
            people = [name for name in people if name]
            points = owner_point.get(str(len(people)))
            if not points:
                return
            for i, name in enumerate(people[: len(points)]):
                ox, oy, osize, ospace = points[i]
                x, y_start = x_base + ox, y_base + oy
                c.setFillColor(colors.black)
                c.setFont("TW-Kai", osize)
                for j, ch in enumerate(name):
                    c.drawString(x, y_start - j * ospace, ch)
            return

        if key == "deceased":
            people = text if isinstance(text, list) else re.split(r"[,\\s]+", str(text).strip())
            people = [name for name in people if name]
            points = deceased_point.get(str(len(people)))
            if not points:
                return

            relations = info.get("relation", [])
            if isinstance(relations, str):
                relations = re.split(r"[,\\s]+", relations.strip())
            if len(relations) < len(people):
                relations += [""] * (len(people) - len(relations))

            for a, b in [("显考", "显妣"), ("祖考", "祖妣")]:
                if a in relations and b in relations:
                    people = list(reversed(people))
                    relations = list(reversed(relations))
                    break

            for i, name in enumerate(people[: len(points)]):
                relation = relations[i] if i < len(relations) else ""
                ox, oy, osize, ospace = points[i]
                x, y_start = x_base + ox, y_base + oy
                c.setFillColor(colors.black)
                c.setFont("TW-Kai", osize)
                for j, ch in enumerate(relation + " " + name):
                    c.drawString(x, y_start - j * ospace, ch)
            return

        if key == "order_id":
            c.setFillColor(colors.black)
            c.setFont("TW-Kai", size)
            c.drawString(x_base, y_base, str(text))
            return

        c.setFillColor(colors.black)
        for i, ch in enumerate(text):
            c.drawString(x_base, y_base - i * spacing, ch)

    items_per_page = len(positions)
    total_items = len(fahui_data)
    for page_start in range(0, total_items, items_per_page):
        drew_on_page = False
        page_order_item_ids = []

        for i, pos in enumerate(positions):
            item_index = page_start + i
            if item_index >= total_items:
                break

            info = fahui_data[item_index]["item_form_data"]
            order_item_id = fahui_data[item_index]["id"]
            order_id = fahui_data[item_index].get("order_id")
            page_order_item_ids.append(order_item_id)

            center = get_point(pos, "center")
            if not center:
                continue
            drew_on_page = True

            base_x, base_y, font_size, spacing = center
            if paiwei_type == "C":
                xiankao = xianbi = " "
                center_text = "冤亲债主"
            elif paiwei_type in ["A1", "B1"]:
                xiankao, xianbi = "显考 ", "显妣 "
                center_text = info.get("surname", "") + info.get("suffix", "门堂上历代祖先")
            elif paiwei_type in ["A2", "B2", "A3", "B3"]:
                xiankao = xianbi = " "
                center_text = "" if paiwei_type in ["A2", "B2"] else " "
            else:
                xiankao, xianbi = "显考 ", "显妣 "
                center_text = info.get("surname", "") + info.get("suffix", "")

            c.setFont("TW-Kai", font_size)
            for j, ch in enumerate(center_text):
                c.drawString(base_x, base_y - j * spacing, ch)

            folichaodu = "佛力超度"
            if paiwei_type in ["A3", "B3"]:
                deceased = info.get("deceased", "")
                if deceased == "无缘子女":
                    deceased = ""
                folichaodu = f"佛力超度 无缘子女{deceased}"

            draw_text_vertical(pos, "folichaodu", folichaodu, base_x, base_y, info)
            draw_text_vertical(pos, "baijian", "拜荐", base_x, base_y, info)
            draw_text_vertical(pos, "lianwei", "莲位", base_x, base_y, info)
            draw_text_vertical(pos, "yangshang", "阳上", base_x, base_y, info)
            draw_text_vertical(pos, "owner", info.get("owner", ""), base_x, base_y, info)
            if info.get("father"):
                draw_text_vertical(pos, "father", f"{xiankao}{info['father']}", base_x, base_y, info)
            if info.get("mother"):
                draw_text_vertical(pos, "mother", f"{xianbi}{info['mother']}", base_x, base_y, info)
            draw_text_vertical(pos, "order_id", str(order_id), base_x, base_y, info)
            if paiwei_type not in ["A3", "B3"]:
                draw_text_vertical(pos, "deceased", info.get("deceased", ""), base_x, base_y, info)

        if drew_on_page:
            if need_barcode:
                existing_pdf = None
                candidate_pdfs = (
                    db.session.query(PrintPDF)
                    .join(PDFPageData)
                    .filter(PDFPageData.order_item_id.in_(page_order_item_ids))
                    .all()
                )
                for pdf in candidate_pdfs:
                    existing_ids = {pd.order_item_id for pd in pdf.page_data}
                    if existing_ids == set(page_order_item_ids):
                        existing_pdf = pdf
                        break

                if existing_pdf:
                    barcode_id = existing_pdf.id
                else:
                    new_pdf = PrintPDF(width=width, height=height)
                    db.session.add(new_pdf)
                    db.session.flush()
                    for oid in page_order_item_ids:
                        db.session.add(PDFPageData(print_pdf_id=new_pdf.id, order_item_id=oid))
                    barcode_id = new_pdf.id

                buf = io.BytesIO()
                img = qrcode.make(str(barcode_id))
                img.save(buf, format="PNG")
                buf.seek(0)
                qr_img = ImageReader(buf)
                c.drawImage(qr_img, 5, 5, width=50, height=50)
                c.setFont("TW-Kai", 10)
                c.setFillColor(colors.black)
                c.drawString(22, 50, str(barcode_id))

            c.showPage()
        db.session.commit()

    c.save()

    final_file_name = f"{source_name}_{paiwei_type}_output.pdf"
    final_pdf_path = os.path.join(output_path, final_file_name)
    overlay_pdf = PdfReader(temp_pdf_path)
    writer = PdfWriter()

    for i in range(len(overlay_pdf.pages)):
        bg_page = PdfReader(bg_pdf_path).pages[0]
        ol_page = overlay_pdf.pages[i]
        merger = PageMerge(bg_page)
        merger.add(ol_page).render()
        writer.addpage(bg_page)

    writer.write(final_pdf_path)
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    return buffer

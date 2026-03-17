import base64
import os
import random

from flask import jsonify, render_template, request, send_file, send_from_directory
from flask_login import login_required
from pdf2image import convert_from_bytes, convert_from_path
from werkzeug.utils import secure_filename

from app.function.common import data_path
from app.function.print_paiwei.blueprint import print_paiwei_bp
from app.function.print_paiwei.generator import (
    generate_paiwei_using_order_ids,
    generate_paiwei_using_order_item_ids,
)
from app.models import Order, OrderItem, PDFPageData, PrintPDF


@print_paiwei_bp.route("/paiwei_config_page", methods=["GET"])
@login_required
def paiwei_config_page():
    return render_template("paiwei_config_page.html")


@print_paiwei_bp.route("/download_app", methods=["GET"])
def download_app():
    folder = os.path.join(data_path, "fahui_app")
    if not os.path.exists(folder):
        return jsonify({"error": "目录不存在"}), 404

    apk_files = [file for file in os.listdir(folder) if file.lower().endswith(".apk")]
    if not apk_files:
        return jsonify({"error": "未找到 APK 文件"}), 404

    apk_files.sort(key=lambda file: os.path.getmtime(os.path.join(folder, file)), reverse=True)
    apk_path = os.path.join(folder, apk_files[0])
    return send_file(apk_path, as_attachment=True, download_name=apk_files[0])


@print_paiwei_bp.route("/get_all_pdf_name", methods=["GET"])
def get_all_pdf_name():
    all_pdf_path = os.path.join(data_path, "pdf_view")
    result = []
    for file in os.listdir(all_pdf_path):
        full_path = os.path.join(all_pdf_path, file)
        if os.path.isfile(full_path):
            result.append({"type": "file", "name": file})
    return jsonify(result)


@print_paiwei_bp.route("/get_pdf_file", methods=["GET"])
def get_pdf_file():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "缺少 filename 参数"}), 400

    pdf_dir = os.path.join(data_path, "pdf_view")
    file_path = os.path.join(pdf_dir, filename)
    if not os.path.isfile(file_path) or not file_path.lower().endswith(".pdf"):
        return jsonify({"error": "文件不存在或不是 PDF"}), 404

    return send_file(file_path, mimetype="application/pdf", as_attachment=False)


@print_paiwei_bp.route("/upload_paiwei_template", methods=["POST"])
@login_required
def upload_paiwei_template():
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return jsonify({"error": "No file uploaded"}), 400
    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not uploaded_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    filename = secure_filename(uploaded_file.filename)
    save_dir = os.path.join(data_path, "paiwei_template")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    uploaded_file.save(save_path)
    return jsonify({"message": "File uploaded successfully", "path": save_path}), 200


@print_paiwei_bp.route("/print_paiwei_order_item/<int:print_pdf_id>", methods=["GET"])
def print_paiwei_order_item(print_pdf_id):
    pdf_obj = PrintPDF.query.get(print_pdf_id)
    if not pdf_obj:
        return jsonify({"status": "error", "message": f"PrintPDF {print_pdf_id} 不存在"}), 404

    page_data = PDFPageData.query.filter_by(print_pdf_id=print_pdf_id).all()
    if not page_data:
        return jsonify({"status": "error", "message": "没有找到对应的 OrderItem"}), 404

    order_item_ids = [page.order_item_id for page in page_data]
    buffer = generate_paiwei_using_order_item_ids(order_item_ids)

    cache_dir = os.path.join(data_path, "paiwei_result", "paiweicache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{print_pdf_id}.jpeg")

    if not os.path.exists(cache_file):
        try:
            images = convert_from_bytes(buffer.getvalue(), first_page=1, last_page=1, fmt="jpeg")
            if not images:
                return jsonify({"status": "error", "message": "PDF 转换失败"}), 500
            images[0].save(cache_file, "JPEG")
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return send_file(cache_file, mimetype="image/jpeg")


@print_paiwei_bp.route("/test_paiwei_image", methods=["POST"])
def test_paiwei_image():
    data = request.get_json() or {}
    paiwei_type = data.get("paiwei_type")
    paiwei_code = data.get("paiwei_code")
    if not paiwei_type or not paiwei_code:
        return jsonify({"status": "error", "message": "缺少 paiwei_type 或 paiwei_code"}), 400

    try:
        limit = int(paiwei_type.split("_")[1])
    except (IndexError, ValueError):
        limit = 1

    order_items = OrderItem.query.filter_by(code=paiwei_code).all()
    if not order_items:
        return jsonify({"status": "error", "message": f"没有找到 code={paiwei_code} 的 OrderItem"}), 404

    random.shuffle(order_items)
    order_item_ids = [item.id for item in order_items[:limit]]
    buffer = generate_paiwei_using_order_item_ids(order_item_ids)
    if not buffer:
        return jsonify({"status": "error", "message": "生成 PDF 失败"}), 500

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"{paiwei_type}_{paiwei_code}.pdf",
    )


@print_paiwei_bp.route("/preview_order/<int:order_id>", methods=["GET"])
def preview_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"status": "error", "message": f"Order {order_id} 不存在"}), 404

    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    if not order_items:
        return jsonify({"status": "error", "message": "没有找到对应的 OrderItem"}), 404

    order_item_ids = [item.id for item in order_items]
    buffer = generate_paiwei_using_order_item_ids(order_item_ids)
    if not buffer:
        return jsonify({"status": "error", "message": "生成 PDF 失败"}), 500

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"order_{order_id}_preview.pdf",
    )


@print_paiwei_bp.route("/generate_by_orders", methods=["POST"])
def generate_by_orders():
    data = request.get_json() or {}
    return generate_paiwei_using_order_ids(
        data.get("order_ids", []),
        need_barcode=data.get("need_barcode", False),
    )


@print_paiwei_bp.route("/download/<filename>", methods=["GET"])
@login_required
def download_file(filename):
    directory = "/home/utba/flaskapp/fahui/database/paiwei_result"
    return send_from_directory(directory, filename, as_attachment=False)


def pdf_to_jpeg(file_path):
    output_dir = os.path.join(data_path, "paiwei_image")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "output_images.jpeg")
    images = convert_from_path(file_path, dpi=300, first_page=1, last_page=1)
    if images:
        images[0].save(output_path, "JPEG")
        return "success"
    return "error"

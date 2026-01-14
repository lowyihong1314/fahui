from datetime import datetime
from flask import send_from_directory,send_file, Response,current_app, Blueprint, jsonify,request,render_template
from flask_login import login_required
from models.fahui import Order,ItemFormData,OrderItem,PrintPDF,PDFPageData
from models import db
import os
from function.config import data_path
from werkzeug.utils import secure_filename
import re

print_paiwei_bp = Blueprint('print_paiwei', __name__)

# 假设你已经有这个 Blueprint 对象
@print_paiwei_bp.route('/paiwei_config_page', methods=['GET'])
@login_required
def paiwei_config_page():
    return render_template('paiwei_config_page.html')

@print_paiwei_bp.route('/download_app', methods=['GET'])
def download_app():
    folder = os.path.join(data_path, 'fahui_app')
    if not os.path.exists(folder):
        return jsonify({"error": "目录不存在"}), 404

    # 找所有 .apk 文件
    apk_files = [f for f in os.listdir(folder) if f.lower().endswith(".apk")]
    if not apk_files:
        return jsonify({"error": "未找到 APK 文件"}), 404

    # 取第一个，按时间排序更合理
    apk_files.sort(key=lambda f: os.path.getmtime(os.path.join(folder, f)), reverse=True)
    apk_path = os.path.join(folder, apk_files[0])

    # 返回文件下载
    return send_file(apk_path, as_attachment=True, download_name=apk_files[0])

# 假设你已经有这个 Blueprint 对象
@print_paiwei_bp.route('/get_all_pdf_name', methods=['GET'])
def get_all_pdf_name():
    all_pdf_path = os.path.join(data_path, 'pdf_view')
    result = []
    for f in os.listdir(all_pdf_path):
        full_path = os.path.join(all_pdf_path, f)
        if os.path.isfile(full_path):
            result.append({'type': 'file', 'name': f})
    return jsonify(result)

@print_paiwei_bp.route('/get_pdf_file', methods=['GET'])
def get_pdf_file():
    # 获取文件名参数
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'error': '缺少 filename 参数'}), 400

    # 构建文件路径
    pdf_dir = os.path.join(data_path, 'pdf_view')
    file_path = os.path.join(pdf_dir, filename)

    # 检查文件是否存在且为 PDF
    if not os.path.isfile(file_path) or not file_path.lower().endswith('.pdf'):
        return jsonify({'error': '文件不存在或不是 PDF'}), 404

    # 发送 PDF 文件
    return send_file(file_path, mimetype='application/pdf', as_attachment=False)

@print_paiwei_bp.route('/upload_paiwei_template', methods=['POST'])
@login_required
def upload_paiwei_template():
    # 获取上传文件
    uploaded_file = request.files.get('file')

    if not uploaded_file:
        return jsonify({'error': 'No file uploaded'}), 400

    if uploaded_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # 检查文件类型
    if not uploaded_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    # 构建保存路径
    filename = secure_filename(uploaded_file.filename)
    save_dir = os.path.join(data_path, 'paiwei_template')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    print(save_path)

    # 保存文件
    uploaded_file.save(save_path)

    return jsonify({'message': 'File uploaded successfully', 'path': save_path}), 200

from pdf2image import convert_from_bytes
import base64

def get_paiwei_data_by_item_ids(order_item_ids):
    """根据多个 order_item_id 获取 paiwei 数据"""
    items = OrderItem.query.filter(OrderItem.id.in_(order_item_ids)).all()
    return [item.to_all_print() for item in items]

@print_paiwei_bp.route('/print_paiwei_order_item/<int:print_pdf_id>', methods=['GET'])
def print_paiwei_order_item(print_pdf_id):
    # ✅ 1. 查 PrintPDF 是否存在
    pdf_obj = PrintPDF.query.get(print_pdf_id)
    if not pdf_obj:
        return jsonify({'status': 'error', 'message': f'PrintPDF {print_pdf_id} 不存在'}), 404

    # ✅ 2. 查找 order_item_ids
    page_data = PDFPageData.query.filter_by(print_pdf_id=print_pdf_id).all()
    if not page_data:
        return jsonify({'status': 'error', 'message': '没有找到对应的 OrderItem'}), 404

    order_item_ids = [pd.order_item_id for pd in page_data]


    buffer = generate_paiwei_using_order_item_ids(order_item_ids)

    # ✅ 6. 缓存目录
    cache_dir = os.path.join(data_path, "paiwei_result", "paiweicache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{print_pdf_id}.jpeg")

    if not os.path.exists(cache_file):
        try:
            images = convert_from_bytes(buffer.getvalue(), first_page=1, last_page=1, fmt='jpeg')
            if not images:
                return jsonify({"status": "error", "message": "PDF 转换失败"}), 500

            images[0].save(cache_file, "JPEG")
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # ✅ 7. 返回图片
    return send_file(cache_file, mimetype="image/jpeg")

from PyPDF2 import PdfMerger
import random
@print_paiwei_bp.route('/test_paiwei_image', methods=['POST'])
def test_paiwei_image():
    data = request.get_json()
    print("收到的 JSON 数据:", data, flush=True)

    paiwei_type = data.get("paiwei_type")  # e.g. paiwei_1
    paiwei_code = data.get("paiwei_code")  # e.g. A1

    if not paiwei_type or not paiwei_code:
        return jsonify({'status': 'error', 'message': '缺少 paiwei_type 或 paiwei_code'}), 400

    # ⚡ 从 "paiwei_1" 里提取数字部分
    try:
        limit = int(paiwei_type.split("_")[1])
    except (IndexError, ValueError):
        limit = 1  # 默认 1

    # ⚡ 先取出所有匹配的 OrderItem
    order_items = OrderItem.query.filter_by(code=paiwei_code).all()
    if not order_items:
        return jsonify({'status': 'error', 'message': f'没有找到 code={paiwei_code} 的 OrderItem'}), 404

    # ⚡ 打乱顺序
    random.shuffle(order_items)

    # ⚡ 截取需要的数量
    order_items = order_items[:limit]

    # 取出 id 列表传给生成函数
    order_item_ids = [item.id for item in order_items]
    print("最终取到的 order_item_ids:", order_item_ids, flush=True)

    buffer = generate_paiwei_using_order_item_ids(order_item_ids)
    if not buffer:
        return jsonify({'status': 'error', 'message': '生成 PDF 失败'}), 500

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"{paiwei_type}_{paiwei_code}.pdf"
    )

@print_paiwei_bp.route('/preview_order/<int:order_id>', methods=['GET'])
def preview_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'status': 'error', 'message': f'Order {order_id} 不存在'}), 404

    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    if not order_items:
        return jsonify({'status': 'error', 'message': '没有找到对应的 OrderItem'}), 404

    order_item_ids = [item.id for item in order_items]

    buffer = generate_paiwei_using_order_item_ids(order_item_ids)
    if not buffer:
        return jsonify({'status': 'error', 'message': '生成 PDF 失败'}), 500

    # 返回 PDF 文件，前端用 pdf.js 渲染
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"order_{order_id}_preview.pdf"
    )

def filter_fahui_data(items):
    """把 OrderItem 列表转换成可打印数据，并过滤掉 code 以 'D' 开头的，且按 item.id 升序"""
    # 按 id 排序
    items_sorted = sorted(items, key=lambda x: x.id)

    fahui_data = [item.to_all_print() for item in items_sorted]
    filtered_data = [item for item in fahui_data if not str(item.get("code", "")).startswith("D")]
    return filtered_data


def generate_paiwei_using_order_item_ids(order_item_ids, need_barcode=False):
    # 1. 查询 OrderItem
    items = OrderItem.query.filter(OrderItem.id.in_(order_item_ids)).all()
    if not items:
        return None  # 没数据

    # 2. 转换数据
    filtered_data = filter_fahui_data(items)
    if not filtered_data:
        return None

    # 3. 按 code 分组
    grouped_data = {}
    for item in filtered_data:
        grouped_data.setdefault(item.get("code"), []).append(item)

    # 4. 循环生成多个 buffer
    merger = PdfMerger()
    for code, items in grouped_data.items():
        point_data, source_name = get_point_data(code)
        if not point_data:
            continue  # 跳过异常 code

        buffer = generate_paiwei(code, items, point_data, source_name, need_barcode=need_barcode)
        buffer.seek(0)
        merger.append(buffer)

    # 5. 合并后的 PDF 输出
    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return output

import zipfile

def generate_paiwei_using_order_ids(order_ids, need_barcode=False):
    # 1. 拿 OrderItem
    items = OrderItem.query.join(Order).filter(Order.id.in_(order_ids)).all()
    if not items:
        return jsonify({'status': 'error', 'message': '没有找到对应的订单数据'}), 400

    # 2. 转换
    filtered_data = filter_fahui_data(items)
    if not filtered_data:
        return jsonify({'status': 'error', 'message': '没有有效的法会数据'}), 400

    # 3. 按 code 分组
    grouped_data = {}
    for item in filtered_data:
        grouped_data.setdefault(item.get('code'), []).append(item)

    # 4. 循环生成 pdf
    buffers = []
    for code, items in grouped_data.items():
        point_data, source_name = get_point_data(code)
        if not point_data:
            return jsonify({'status': 'error', 'message': f'⚠️ 找不到 point_data 对应 code: {code}'}), 400

        buffer = generate_paiwei(code, items, point_data, source_name, need_barcode=need_barcode)
        buffers.append((code, buffer))

    # 5. 打包 zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for code, buffer in buffers:
            zipf.writestr(f"paiwei_{code}.pdf", buffer.getvalue())

    zip_buffer.seek(0)

    # ✅ send_file 会自动带 Content-Length，前端能看到下载进度
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="paiwei_files.zip"
    )

import io

@print_paiwei_bp.route("/generate_by_orders", methods=["POST"])
def generate_by_orders():
    data = request.get_json()
    order_ids = data.get("order_ids", [])
    need_barcode = data.get("need_barcode", False)
    return generate_paiwei_using_order_ids(order_ids, need_barcode=need_barcode)



@print_paiwei_bp.route('/download/<filename>', methods=['GET'])
@login_required
def download_file(filename):
    # 指定保存 PDF 的路径
    directory = '/home/utba/flaskapp/fahui/database/paiwei_result'

    # 发送文件给浏览器
    return send_from_directory(directory, filename, as_attachment=False)

def get_point_data(paiwei_type):
    # 根据牌位类型选择模板名
    if paiwei_type in ('A1', 'A2', 'A3'):
        souce_name = 'paiwei_1'
    elif paiwei_type in ('B1', 'B2', 'B3'):
        souce_name = 'paiwei_5'
    elif paiwei_type == 'C':
        souce_name = 'paiwei_10'
    else:
        return None, None  # 或 raise ValueError("Invalid type")

    # JSON 文件路径
    json_file_path = os.path.join(data_path, 'point.json')

    # 加载 JSON 数据
    with open(json_file_path, 'r', encoding='utf-8') as f:
        point_data = json.load(f)

    # 查找对应 souce_name 的内容
    for entry in point_data:
        if souce_name in entry:
            result = entry[souce_name]
            return result, souce_name

    # 如果没找到
    return None, souce_name


from reportlab.lib.pagesizes import A4, landscape
import os
import re
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.graphics.barcode import code128
from io import BytesIO
from pdfrw import PdfReader, PdfWriter, PageMerge
import qrcode
from reportlab.lib.utils import ImageReader

def get_owner_point(owner_point):
    json_file_path = os.path.join(data_path, f'{owner_point}.json')
    with open(json_file_path, 'r', encoding='utf-8') as f:
        owner_point = json.load(f)
    return owner_point

def get_deceased_point(file_key):
    json_file_path = os.path.join(data_path, f'{file_key}.json')
    with open(json_file_path, 'r', encoding='utf-8') as f:
        deceased_point = json.load(f)
    return deceased_point

def generate_paiwei(paiwei_type,fahui_data, point_data, souce_name,need_barcode=False):
    print(fahui_data)
    # 处理 A3 或 B3 的特殊逻辑
    if paiwei_type in ['A3', 'B3']:
        for item in fahui_data:
            form_data = item.get('item_form_data', {})
            owner_list = []

            if 'mother' in form_data:
                val = form_data.pop('mother')
                if isinstance(val, list):
                    owner_list.extend([f"母 {v}" for v in val])
                else:
                    owner_list.append(f"母 {val}")
            if 'father' in form_data:
                val = form_data.pop('father')
                if isinstance(val, list):
                    owner_list.extend([f"父 {v}" for v in val])
                else:
                    owner_list.append(f"父 {val}")
            if owner_list:
                form_data['owner'] = owner_list

            item['item_form_data'] = form_data
    # 打印处理后的数据，方便验证

    buffer = BytesIO()
    output_path = os.path.join(data_path, 'paiwei_result')
    os.makedirs(output_path, exist_ok=True)

    file_name = f'{souce_name}.pdf'
    bg_pdf_path = os.path.join(data_path, 'paiwei_template', file_name)

    # 注册字体
    font_path = os.path.join(data_path, 'kai.ttf')
    pdfmetrics.registerFont(TTFont('TW-Kai', font_path))
    # 判断页面方向
    if souce_name == 'paiwei_5':
        page_size = landscape(A4)  # 横向 A4
        owner_point = get_owner_point('owner_point_B')
        deceased_point = get_deceased_point('deceased_point_B')
    elif souce_name == 'paiwei_1':
        page_size = A4  # 纵向 A4
        owner_point = get_owner_point('owner_point_A')
        deceased_point = get_deceased_point('deceased_point_A')
    else:
        page_size = A4  # 纵向 A4
        owner_point = get_owner_point('owner_point_C')
        deceased_point = get_deceased_point('deceased_point_C')


    temp_pdf_path = os.path.join(output_path, f'{souce_name}_temp_text_{paiwei_type}.pdf')
    c = canvas.Canvas(temp_pdf_path, pagesize=page_size)
    width, height = page_size  # 更新宽高变量

    # 整理点位
    point_dict = {}
    for block in point_data:
        point_dict.update(block)

    def get_point(block_key, key):
        for pt in point_dict.get(block_key, []):
            if f"{key}_point" in pt:
                return pt[f"{key}_point"]
        return None

    positions = sorted(point_dict.keys())  # 排序如 ['A', 'B', 'C', ...]


    def draw_text_vertical(block_key, key, text, base_x, base_y):
        pt = get_point(block_key, key)

        if not pt:
            return

        dx, dy, size, spacing = pt
        x_base, y_base = base_x + dx, base_y + dy
        c.setFont('TW-Kai', size)

        # ---- owner 动态点位 ----
        if key == 'owner':
            people = text if isinstance(text, list) else re.split(r'[,\s]+', str(text).strip())
            people = [name for name in people if name]
            count = len(people)

            if not (0 < count <= 6):
                return

            points = owner_point.get(str(count))
            if not points:
                return

            for i, name in enumerate(people[:len(points)]):
                ox, oy, osize, ospace = points[i]
                x, y_start = x_base + ox, y_base + oy

                # c.setFillColor(colors.red)
                # c.circle(x, y_start, 2, fill=1)

                c.setFillColor(colors.black)
                c.setFont('TW-Kai', osize)
                for j, ch in enumerate(name):
                    c.drawString(x, y_start - j * ospace, ch)
            return

        # ---- deceased 动态点位 ----
        if key == 'deceased':
            people = text if isinstance(text, list) else re.split(r'[,\s]+', str(text).strip())
            people = [name for name in people if name]
            count = len(people)

            if not (0 < count <= 6):
                return

            # 取 relation（和 deceased 对应的数量一致）
            relations = info.get('relation', [])
            # 保证 relation 数量和 people 对齐，不足时补空
            if isinstance(relations, str):
                relations = re.split(r'[,\s]+', relations.strip())
            if len(relations) < count:
                relations += [""] * (count - len(relations))

            pairs = [
                ("显考", "显妣"),
                ("祖考", "祖妣"),
            ]

            for a, b in pairs:
                if a in relations and b in relations:
                    people = list(reversed(people))
                    relations = list(reversed(relations))
                    break


            points = deceased_point.get(str(count))
            if not points:
                return

            for i, name in enumerate(people[:len(points)]):
                relation = relations[i] if i < len(relations) else ""
                ox, oy, osize, ospace = points[i]
                x, y_start = x_base + ox, y_base + oy

                # # 红点标记
                # c.setFillColor(colors.red)
                # c.circle(x, y_start, 2, fill=1)

                # 黑色文字
                c.setFillColor(colors.black)
                c.setFont('TW-Kai', osize)

                # ⚡ 竖排：先画 relation，再画姓名
                full_text = relation + " " + name
                for j, ch in enumerate(full_text):
                    c.drawString(x, y_start - j * ospace, ch)
            return
        if key == 'order_id':
            c.setFillColor(colors.black)
            c.setFont('TW-Kai', size)
            print(f'printing:{text}')
            c.drawString(x_base, y_base, str(text))  # 横向整串打印
            return

        # ---- 普通字段 ----

        c.setFillColor(colors.blue)
        # c.circle(x_base, y_base, 2, fill=1)
        c.setFillColor(colors.black)
        for i, ch in enumerate(text):
            c.drawString(x_base, y_base - i * spacing, ch)

    item_index = 0
    total_items = len(fahui_data)

    items_per_page = len(positions)  # 比如 ['A', 'B'] => 2

    page_number = 1

    for page_start in range(0, total_items, items_per_page):

        drew_on_page = False
        page_order_item_ids = []

        for i, pos in enumerate(positions):

            item_index = page_start + i
            if item_index >= total_items:
                break

            info = fahui_data[item_index]['item_form_data']
            order_item_id = fahui_data[item_index]['id']
            page_order_item_ids.append(order_item_id)
            order_id = fahui_data[item_index].get('order_id')


            center = get_point(pos, 'center')
            if not center:
                print(f"⚠️ 点位 {pos} 缺少 center_point，跳过。")
                continue

            drew_on_page = True  # ✅ 只要画了中心点就算这一页有内容

            base_x, base_y, font_size, spacing = center
            if paiwei_type == "C":
                xiankao = " "
                xianbi = " "
                center_text = ('冤亲债主')
            elif paiwei_type in ['A1', 'B1']:
                xiankao = "显考 "
                xianbi = "显妣 "
                center_text = info.get('surname', '') + info.get('suffix', '门堂上历代祖先')
            elif paiwei_type in ['A2', 'B2']:
                xiankao = " "
                xianbi = " "
                center_text = ""
            elif paiwei_type in ['A3', 'B3']:
                xiankao = " "
                xianbi = " "
                center_text = " "
            else:
                xiankao = "显考 "
                xianbi = "显妣 "
                center_text = info.get('surname', '') + info.get('suffix', center_text)
            c.setFont('TW-Kai', font_size)
            for j, ch in enumerate(center_text):
                y = base_y - j * spacing
                c.drawString(base_x, y, ch)

            folichaodu = '佛力超度'
            if paiwei_type in ['A3', 'B3']:
                deceased = info.get('deceased','')
                if deceased == '无缘子女':
                    deceased = ''
                folichaodu = f'佛力超度 无缘子女{deceased}'

            draw_text_vertical(pos, 'folichaodu', folichaodu, base_x, base_y)
            draw_text_vertical(pos, 'baijian', '拜荐', base_x, base_y)
            draw_text_vertical(pos, 'lianwei', '莲位', base_x, base_y)
            draw_text_vertical(pos, 'yangshang', '阳上', base_x, base_y)
            draw_text_vertical(pos, 'owner', info.get('owner', ''), base_x, base_y)
            if info.get("father"):
                draw_text_vertical(pos, 'father', f"{xiankao}{info['father']}", base_x, base_y)

            if info.get("mother"):
                draw_text_vertical(pos, 'mother', f"{xianbi}{info['mother']}", base_x, base_y)
            draw_text_vertical(pos, 'order_id', str(order_id), base_x, base_y)

            if paiwei_type not in ['A3', 'B3']:
                draw_text_vertical(pos, 'deceased', info.get('deceased', ''), base_x, base_y)
         
        if drew_on_page:
            
            if need_barcode:
                # ⚡️ 先检查是否已有对应的 PrintPDF
                existing_pdf = None
                # 找到所有包含这些 order_item_id 的 pdf 记录
                candidate_pdfs = (
                    db.session.query(PrintPDF)
                    .join(PDFPageData)
                    .filter(PDFPageData.order_item_id.in_(page_order_item_ids))
                    .all()
                )

                for pdf in candidate_pdfs:
                    existing_ids = {pd.order_item_id for pd in pdf.page_data}
                    if existing_ids == set(page_order_item_ids):  # ⚡️ 完全一致
                        existing_pdf = pdf
                        break

                if existing_pdf:
                    new_pdf = existing_pdf
                    barcode_id = new_pdf.id
                else:
                    # ✅ 创建新的 PrintPDF
                    new_pdf = PrintPDF(width=width, height=height)
                    db.session.add(new_pdf)
                    db.session.flush()

                    # 新建 page_data
                    for oid in page_order_item_ids:
                        new_page_data = PDFPageData(print_pdf_id=new_pdf.id, order_item_id=oid)
                        db.session.add(new_page_data)

                    barcode_id = new_pdf.id

                # ⚡️ 判断页面横纵向，计算位置
                if width > height:  # 横向
                    barcode_x, barcode_y = 0, 0
                else:  # 纵向
                    barcode_x, barcode_y = 0, 0

                buf = io.BytesIO()
                img = qrcode.make(str(barcode_id))
                img.save(buf, format="PNG")
                buf.seek(0)
                qr_img = ImageReader(buf)
                c.drawImage(qr_img, barcode_x +5, barcode_y +5, width=50, height=50)
                # 条形码上方加文字（打印数字 ID）
                c.setFont("TW-Kai", 10)
                c.setFillColor(colors.black)
                c.drawString(barcode_x + 22, barcode_y + 50, str(barcode_id))

            c.showPage()

            page_number += 1
        db.session.commit()  # 提交数据库更改，保存 PrintPDF 和 PDFPageData 记录
    c.save()

    final_file_name = f'{souce_name}_{paiwei_type}_output.pdf'
    final_pdf_path = os.path.join(output_path, final_file_name)

    overlay_pdf = PdfReader(temp_pdf_path)
    writer = PdfWriter()

    buffer = BytesIO()

    for i in range(len(overlay_pdf.pages)):
        # 每次重新读取模板页，确保是新对象
        bg_page = PdfReader(bg_pdf_path).pages[0]
        ol_page = overlay_pdf.pages[i]
        merger = PageMerge(bg_page)
        merger.add(ol_page).render()
        writer.addpage(bg_page)

    # ⚡️ 1. 写入磁盘
    writer.write(final_pdf_path)

    # ⚡️ 2. 写入内存 buffer
    buffer = BytesIO()
    writer.write(buffer)
    buffer.seek(0)  # 👈 这一句很重要

    return buffer

import json
@print_paiwei_bp.route('/get_point_json', methods=['GET'])
@login_required
def get_point_json():
    json_file_path = os.path.join(data_path, 'point.json')
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return jsonify(data)

@print_paiwei_bp.route('/update_point_json', methods=['POST'])
@login_required
def update_point_json():
    json_file_path = os.path.join(data_path, 'point.json')
    
    try:
        # 获取前端传来的 JSON 数据
        new_data = request.get_json()

        # 写入文件（覆盖原来的）
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)

        return jsonify({"success": True, "message": "point.json 更新成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


from models.fahui import OrderItem
def get_paiwei_data(order_id_list):
    # 获取所有符合条件的 Order（订单）
    orders = Order.query.filter(Order.id.in_(order_id_list)).all()

    # 从每个订单中提取其所有 OrderItem
    results = []
    for order in orders:
        results.extend(order.order_items)  # 拼接每个订单的所有 items

    # 返回格式化后的结果
    data = [item.to_all_print() for item in results]
    return data


from pdf2image import convert_from_path
def pdf_to_jpeg(file_path):

    file_name = f'output_images'
    # 输出图片目录和文件名（.pdf 改为 .jpeg）
    output_dir = os.path.join(data_path, 'paiwei_image')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"{file_name}.jpeg")

    # 转换 PDF 的第一页为图像（dpi 可根据需要调整）
    images = convert_from_path(file_path, dpi=300, first_page=1, last_page=1)

    if images:
        images[0].save(output_path, 'JPEG')
        return 'success'
    else:
        return 'error'
    

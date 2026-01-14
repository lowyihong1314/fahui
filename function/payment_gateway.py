import os
from flask import request, jsonify, Blueprint
from flask_login import current_user,login_required
from sqlalchemy import func
from datetime import datetime
from werkzeug.utils import secure_filename
from function.config import data_path,parent_dir
from models import db

from models.fahui import Order,ItemFormData,OrderItem
from models.payment_data import PaymentData

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import make_response
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from flask import send_file

payment_bp = Blueprint('payment', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@payment_bp.route('/make_payment/<int:order_id>', methods=['POST'])
def make_payment(order_id):
    payment_mode = request.form.get('payment_mode') or request.json.get('payment_mode')
    file = request.files.get('file')  # 上传文件

    # 校验支付方式
    if not payment_mode:
        return jsonify({'success': False, 'message': '缺少 payment_mode'}), 400

    if not current_user.is_authenticated:
        # 未登录用户 → 必须上传文件
        if payment_mode in ['bank', 'qr']:
            if not file:
                return jsonify({'success': False, 'message': '未登录用户必须上传文件'}), 400
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'message': '文件类型不允许'}), 400
            
    order = db.session.query(Order).filter_by(id=order_id).first()
    if not order:
        return jsonify({'success': False, 'message': '订单不存在'}), 404
    if order.version != '2025_YLP':
        return jsonify({'success': False, 'message': '订单版本已过期'}), 400
    
    # 获取订单总金额
    total_amount = db.session.query(func.sum(OrderItem.price)) \
        .filter(OrderItem.order_id == order_id).scalar() or 0

    # 如果上传文件，保存文件
    document_path = None
    if file:
        filename_ext = file.filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        filename = f"{order_id}_{timestamp}.{filename_ext}"
        save_dir = os.path.join(data_path, 'payment')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)
        file.save(save_path)
        document_path = os.path.relpath(save_path)  # 可选：只保存相对路径

    # 构建 PaymentData 实例
    payment = PaymentData(
        order_id=order_id,
        total_price=total_amount,
        payment_mode=payment_mode,
        document=document_path,
        status='panding',
        created_at=datetime.utcnow()
    )


    db.session.add(payment)
    db.session.commit()

    return jsonify({'success': True, 'message': '支付记录已保存', 'payment_id': payment.id})

@payment_bp.route('/get_all_payment_data', methods=['GET'])
@login_required
def get_all_payment_data():
    payments = PaymentData.query.order_by(PaymentData.created_at.desc()).all()
    
    result = []
    for payment in payments:
        result.append(payment.to_dict_full())
    return jsonify({'success': True, 'data': result})

@payment_bp.route('/get_payment_data/<int:order_id>', methods=['GET'])
def get_payment_data_by_order(order_id):
    payments = PaymentData.query.filter_by(order_id=order_id).order_by(PaymentData.created_at.desc()).all()

    if not payments:
        return jsonify({'success': False, 'message': '该订单没有支付记录'}), 404

    result = []
    for payment in payments:
        result.append({
            'id': payment.id,
            'order_id': payment.order_id,
            'total_price': payment.total_price,
            'payment_mode': payment.payment_mode,
            'document': payment.document,
            'status': payment.status,
            'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'valid_by': payment.valid_by,
            'valid_at': payment.valid_at.strftime('%Y-%m-%d %H:%M:%S') if payment.valid_at else None,
            "login": True if current_user and current_user.is_authenticated else False
        })

    return jsonify({'success': True, 'data': result})

@payment_bp.route('/calculate_amount/<int:id>', methods=['GET'])
def calculate_amount(id):
    # 查询该订单下的所有 OrderItem
    items = OrderItem.query.filter_by(order_id=id).all()

    total_amount = 0
    for item in items:
        item_dict = item.to_dict()  # ✅ 复用已有逻辑
        total_amount += item_dict.get("price", 0) or 0

    return jsonify({'amount': total_amount})

field_label = {
    'father': '父',
    'mother': '母',
    'owner': '阳上',
    'relation': '关系',
    'suffix': '字段',
    'surname': '姓氏',
    'deceased': '亡者姓名',
    'price': '金额',
    'quantity':'数量',
}

def get_label_cn_filter(value):
    for key in field_label:
        if value.startswith(key):
            return field_label[key]
    return value

@payment_bp.route('/download_quotiton/<int:order_id>', methods=['GET'])
def download_quotation_reportlab(order_id):
    total_amount = db.session.query(func.sum(OrderItem.price)) \
        .filter(OrderItem.order_id == order_id).scalar()

    if total_amount is None:
        total_amount = 0

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order_detail = order.to_all_detail()

    font_path = os.path.join(data_path, 'kai.ttf')
    pdfmetrics.registerFont(TTFont('TW-Kai', font_path))

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 画 logo，保持1:1比例（例如60x60）
    logo_path = os.path.join(data_path, 'logo/logo.png')
    try:
        logo = ImageReader(logo_path)
        logo_size = 60
        c.drawImage(logo, 50, height - logo_size - 20, width=logo_size, height=logo_size, mask='auto')
    except Exception as e:
        print(f"Failed to load logo image: {e}")

    # logo 右边加大字号标题
    c.setFont('TW-Kai', 28)
    c.drawString(120, height - 55, "地南佛学会")

    y = height - 100  # logo 和标题下方开始

    c.setFont('TW-Kai', 16)

    y -= 30

    c.setFont('TW-Kai', 12)
    c.drawString(50, y, f"功德主: {order_detail['customer_name']}")
    y -= 20
    c.drawString(50, y, f"联系电话: {order_detail['phone']}")
    y -= 20
    c.drawString(50, y, f"订单编号: {order_detail['id']}")
    y -= 20
    c.drawString(50, y, f"创建日期: {order_detail['created_at']}")
    y -= 20
    c.drawString(50, y, f" ")
    y -= 40

    # 美化订单项目标题区域
    title_box_height = 40
    c.setFillColorRGB(0.9, 0.9, 0.95)  # 淡淡蓝色背景
    c.rect(45, y - title_box_height + 10, width - 90, title_box_height, fill=1, stroke=0)
    c.setFillColor(colors.black)

    y -= 10
    c.setFont('TW-Kai', 14)
    c.drawString(50, y, "订单项目")
    y -= 30

    # 表头加粗并画线
    c.setFont('TW-Kai', 12)
    c.setLineWidth(1)
    c.setStrokeColor(colors.grey)
    c.drawString(50, y, "项目名称")
    c.drawString(250, y, "德金 (RM)")
    c.drawString(350, y, "相关信息")

    y -= 5
    c.line(45, y, width - 45, y)
    y -= 15

    c.setFont('TW-Kai', 12)
    for item in order_detail['order_items']:
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont('TW-Kai', 12)

        c.drawString(50, y, item['item_name'])
        price = item['price']
        c.drawString(250, y, f'{price:.0f}')

        y_related = y

        for key, val_list in item['item_form_data'].items():
            if key == 'price':
                continue
            vals = ', '.join(v['val'] for v in val_list)
            c.drawString(350, y_related, f"{get_label_cn_filter(key)}: {vals}")
            y_related -= 15


        y = y_related - 10

    if y < 50:
        c.showPage()
        y = height - 50
        c.setFont('TW-Kai', 12)

    c.setFont('TW-Kai', 14)
    c.drawString(50, y, f"总德金 (RM): {total_amount:.0f}")

    c.save()
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=order_{order_id}_quotation.pdf'
    return response


@payment_bp.route('/update_payment_status/<int:payment_id>', methods=['POST'])
@login_required
def update_payment_status(payment_id):
    data = request.get_json()
    status = data.get('status')

    if status not in ['approve', 'reject', 'panding']:
        return jsonify({'success': False, 'message': '无效的状态'})

    payment = PaymentData.query.get(payment_id)
    if not payment:
        return jsonify({'success': False, 'message': '找不到该记录'})

    # 更新 PaymentData
    payment.status = status
    payment.valid_by = current_user.username
    payment.valid_at = datetime.utcnow()

    # 如果是 approve，同步更新 Order 表状态为 paid
    if status == 'approve':
        order = Order.query.get(payment.order_id)
        if order:
            order.status = 'paid'

    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@payment_bp.route('/get_payment_detail/<int:id>', methods=['GET'])
def get_payment_detail(id):
    payment = PaymentData.query.get(id)
    if not payment:
        return jsonify({'success': False, 'message': '支付记录不存在'}), 404
    if not hasattr(payment, 'to_dict_full'):
        return jsonify({'success': False, 'message': '未实现 to_dict_full 方法'}), 500
    return jsonify({'success': True, 'data': payment.to_dict_full()})

@payment_bp.route('/get_payment_image/<int:id>', methods=['GET'])
def get_payment_image(id):
    payment = PaymentData.query.get(id)
    if not payment or not payment.document:
        return jsonify({'success': False, 'message': '图片不存在'}), 404

    # 构建图片的绝对路径
    document_path = os.path.join(parent_dir, payment.document)
    if not os.path.isfile(document_path):
        return jsonify({'success': False, 'message': '文件未找到'}), 404

    # 获取文件扩展名，设置正确的 mimetype
    ext = payment.document.rsplit('.', 1)[-1].lower()
    mimetype = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'pdf': 'application/pdf'
    }.get(ext, 'application/octet-stream')

    return send_file(document_path, mimetype=mimetype, as_attachment=False, download_name=os.path.basename(document_path))


PRINTER_IP = "192.168.68.43"
PRINTER_PORT = 9100

# -*- coding: utf-8 -*-
from flask import jsonify
from datetime import datetime
import socket

def _escpos_init():
    return b"\x1b\x40"  # ESC @ 初始化

def _escpos_align(mode="left"):
    mp = {"left": 0, "center": 1, "right": 2}
    return b"\x1b\x61" + bytes([mp.get(mode, 0)])

def _escpos_bold(on=True):
    return b"\x1b\x45" + (b"\x01" if on else b"\x00")

def _escpos_size(w=1, h=1):
    # GS ! n, 高4位倍高，低4位倍宽；1~8倍：0=1倍
    w = max(1, min(8, w)) - 1
    h = max(1, min(8, h)) - 1
    n = (h << 4) | w
    return b"\x1d\x21" + bytes([n])

def _escpos_cut():
    return b"\x1d\x56\x41\x00"  # 全切

def _escpos_hr(char="-", width=45):
    line = (char * width) + "\n"
    return line.encode("gb18030", errors="ignore")

def _send_raw_to_printer(data_bytes: bytes):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(5)
        s.connect((PRINTER_IP, PRINTER_PORT))
        s.sendall(data_bytes)
        s.shutdown(socket.SHUT_WR)

def _fmt_money(v):
    try:
        return f"{float(v or 0):.2f}"
    except:
        return "0.00"

def _wrap_text(text, width=22):
    # 简单等宽切割（中文字宽按1算，足够应付）
    text = text or ""
    out = []
    line = ""
    for ch in text:
        line += ch
        if len(line) >= width:
            out.append(line)
            line = ""
    if line:
        out.append(line)
    return out

fahui_type = {
    'A1': '大牌位_超度历代祖先',
    'A2': '大牌位_超度亡灵',
    'A3': '大牌位_无缘子女',
    'B1': '小牌位_超度历代祖先',
    'B2': '小牌位_超度亡灵',
    'B3': '小牌位_无缘子女',
    'D1': '普度贡品',
    'C': '超度冤亲债主',
    'D': '随缘供斋'
}

def get_fahui_type(value):
    return fahui_type.get(value, value)


def _build_receipt_bytes(order: 'Order', payment: 'PaymentData|None'=None) -> bytes:
    L_WIDTH = 18  # 左侧内容宽度
    R_WIDTH = 8   # 右侧金额宽度
    LINE_WIDTH = 35  # 每行总宽度

    b = bytearray()
    b += _escpos_init()

    # 标题
    b += _escpos_align("center")
    b += _escpos_bold(True) + _escpos_size(2, 2)
    b += "地南佛学会\n".encode("gb18030", errors="ignore")
    b += _escpos_bold(False) + _escpos_size(1, 1)

    # 基本信息
    b += _escpos_align("left")
    created = order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else ""
    b += f"单号: {order.id}\n".encode("gb18030", errors="ignore")
    b += f"时间: {created}\n".encode("gb18030", errors="ignore")
    b += f"施主: {order.customer_name or ''}\n".encode("gb18030", errors="ignore")
    b += f"电话: {order.phone or ''}\n".encode("gb18030", errors="ignore")
    if payment:
        b += f"支付方式: {payment.payment_mode or '-'}\n".encode("gb18030", errors="ignore")
        b += f"单据号: {payment.document or '-'}\n".encode("gb18030", errors="ignore")

    b += _escpos_hr("-")

    # 明细
    total = 0.0
    # 存储按 print_pdf_id 分类的板信息
    print_pdf_groups = {}

    for it in (order.order_items or []):
        name = get_fahui_type(it.code)
        price = _fmt_money(it.price)

        # 处理名称换行
        lines = _wrap_text(name, width=L_WIDTH)
        if not lines:
            lines = [""]
        
        # 第1行拼接：名称 + 金额
        left = lines[0]
        # 保证价格右对齐
        space = LINE_WIDTH - len(left) - len(price)
        space = max(1, space)
        b += (left + (" " * space) + price + "\n").encode("gb18030", errors="ignore")

        # 后续行只打印名称，保持格式一致
        for cont in lines[1:]:
            b += (cont + (" " * (LINE_WIDTH - len(cont)) + "\n")).encode("gb18030", errors="ignore")

        total += float(it.price or 0)

        # 获取与 OrderItem 相关的 BoardData
        for pdf_page in it.pdf_pages:  # 遍历与订单项关联的 PDF 页面数据
            # 获取 print_pdf_id 来查找 BoardData
            print_pdf = pdf_page.print_pdf
            if print_pdf:
                for board_data in print_pdf.boards:  # 获取 BoardData
                    board_header = board_data.board  # 获取 BoardHeader
                    # 计算行号和列号
                    row = (board_data.location - 1) // board_header.board_width + 1  # 行号
                    col = (board_data.location - 1) % board_header.board_width + 1  # 列号

                    # 从 item_form_data 获取 owner 或 deceased 信息
                    owner_or_deceased = None
                    if it.item_form_data:
                        # 优先查找 owner 字段，再查找 deceased 字段
                        for fd in it.item_form_data:
                            if fd.field_name == "owner":
                                owner_or_deceased = fd.field_value
                                break
                        if not owner_or_deceased:
                            for fd in it.item_form_data:
                                if fd.field_name == "deceased":
                                    owner_or_deceased = fd.field_value
                                    break

                    # 将每个 print_pdf_id 作为 key 分类
                    if print_pdf.id not in print_pdf_groups:
                        print_pdf_groups[print_pdf.id] = []

                    print_pdf_groups[print_pdf.id].append({
                        "board_name": board_header.board_name,
                        "location": board_data.location,
                        "row": row,  # 行号
                        "col": col,  # 列号
                        "owner_or_deceased": owner_or_deceased,  # 施主/故人
                    })

    # 打印按 print_pdf_id 分组的板信息
    for print_pdf_id, boards in print_pdf_groups.items():
        b += _escpos_align("left")
        b += _escpos_hr("-")  # 每个 print_pdf_id 的分组下加一条横
        b += f"QR: {print_pdf_id}\n".encode("gb18030", errors="ignore")

        # 我们需要检查 board_name 和 location 是否重复
        printed_boards = set()  # 用于存储已打印的 (board_name, location) 组合
        for board in boards:
            board_key = (board['board_name'], board['location'])
            if board_key not in printed_boards:
                b += f"板名: {board['board_name']}\n".encode("gb18030", errors="ignore")
                b += f"位置: 第{board['row']}排，第{board['col']}个\n".encode("gb18030", errors="ignore")
                printed_boards.add(board_key)  # 标记该板已经打印过
            if board['owner_or_deceased']:  # 如果有 owner 或 deceased 信息
                b += f"施主/故人: {board['owner_or_deceased']}\n".encode("gb18030", errors="ignore")
        b += _escpos_hr("-")  # 在每个板信息之后加一条横线

    b += _escpos_hr("=")  # 添加结算部分的横线

    # 合计（加粗）
    b += _escpos_bold(True)
    total_str = _fmt_money(total)
    label = "合计"
    space = LINE_WIDTH - len(label) - len(total_str)
    space = max(1, space)
    b += (label + (" " * space) + total_str + "\n").encode("gb18030", errors="ignore")
    b += _escpos_bold(False)

    b += _escpos_hr("-")
    b += _escpos_align("center")
    b += "感谢您的随喜，功德无量\n".encode("gb18030", errors="ignore")
    b += "\n\n".encode("gb18030", errors="ignore")
    b += _escpos_cut()

    return bytes(b)

@payment_bp.route('/print_receipt/<int:order_id>', methods=['POST'])
@login_required
def print_receipt(order_id):
    """
    直接把订单收据打印到 192.168.68.43:9100（80mm热敏 ESC/POS）
    """
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404

        # 取最新支付记录（可选）
        payment = None
        if order.payments:
            payment = max(order.payments, key=lambda p: p.created_at)
        
        payload = _build_receipt_bytes(order, payment)
        _send_raw_to_printer(payload)

        return jsonify({'success': True, 'message': f'订单 {order_id} 收据已发送到打印机'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

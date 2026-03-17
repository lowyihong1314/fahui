import os
from flask import request, jsonify, Blueprint
from flask_login import current_user,login_required
from sqlalchemy import func
from datetime import datetime
from app.function.common import data_path, flask_path
from app.function.payment.service import allowed_file, get_label_cn_filter
from app.function.payment.reports import build_quotation_response
from app.function.payment.receipt import build_receipt_bytes, send_raw_to_printer
from app.extensions import db

from app.models import ItemFormData, Order, OrderItem
from app.models.payment_data import PaymentData

from flask import send_file
from app.services.payment_service import PaymentService

payment_bp = Blueprint('payment', __name__)

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
        result.append(PaymentService.to_dict_full(payment))
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

@payment_bp.route('/download_quotiton/<int:order_id>', methods=['GET'])
def download_quotation_reportlab(order_id):
    return build_quotation_response(order_id)


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
    return jsonify({'success': True, 'data': PaymentService.to_dict_full(payment)})

@payment_bp.route('/get_payment_image/<int:id>', methods=['GET'])
def get_payment_image(id):
    payment = PaymentData.query.get(id)
    if not payment or not payment.document:
        return jsonify({'success': False, 'message': '图片不存在'}), 404

    # 构建图片的绝对路径
    document_path = os.path.join(flask_path, payment.document)
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
        
        payload = build_receipt_bytes(order, payment)
        send_raw_to_printer(payload)

        return jsonify({'success': True, 'message': f'订单 {order_id} 收据已发送到打印机'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

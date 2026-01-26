from datetime import datetime
from flask import send_file, current_app, Blueprint, jsonify,request
from flask_login import login_required,current_user
from app.models.fahui import Order,ItemFormData,OrderItem,PrintPDF,PDFPageData,BoardData,BoardHeader
from app.extensions import db
from app.function.config import verification_required
from sqlalchemy import text

from app.services.order_service import OrderService
from app.services.board_service import BoardService

fahui_router_bp = Blueprint('fahui_router', __name__)

@fahui_router_bp.route("/search", methods=["GET"])
def search():

    # ===== 参数读取 =====
    version = request.args.get("version", type=int)
    value = request.args.get("value", default="", type=str)
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)

    # ===== 基础参数校验 =====
    if version is None:
        return jsonify({
            "status": "error",
            "message": "version is required"
        }), 400

    # ===== 调用 Service =====
    result = OrderService.search_orders(
        version=version,
        value=value,
        page_num=page,
        per_page=per_page
    )

    # ===== 返回统一结构 =====
    return jsonify({
        "status": "success",
        "data": result
    })

@fahui_router_bp.route("/get_order_by_id", methods=["GET"])
def get_order_by_id():
    # ===== 参数读取 =====
    order_id = request.args.get("order_id", type=int) or request.args.get("id", type=int)

    # ===== 参数校验 =====
    if not order_id:
        return jsonify({
            "status": "error",
            "message": "order_id is required"
        }), 400

    # ===== 查询订单详情 =====
    order_data = OrderService.to_all_detail(order_id)
    if not order_data:
        return jsonify({
            "status": "error",
            "message": f"找不到订单 ID {order_id}"
        }), 404

    # ===== 返回统一结构 =====
    return jsonify({
        "status": "success",
        "data": order_data
    })

@fahui_router_bp.route('/new_customer', methods=['POST'])
def new_customer():
    data = request.get_json() or {}

    name = data.get('name')
    phone = data.get('phone')
    version = '2025_YLP'

    try:
        # =========================
        # 1️⃣ 幂等检查：是否已存在
        # =========================
        existing_order = (
            db.session.query(Order)
            .filter(
                Order.name == name,
                Order.phone == phone,
                Order.version == version,
            )
            .first()
        )

        if existing_order:
            # ⭐ 已存在：直接返回旧数据
            order_dict = OrderService.to_dict(existing_order)
            return jsonify({
                'success': True,
                'message': '订单已存在',
                'order': order_dict,
                'duplicated': True
            })

        # =========================
        # 2️⃣ 不存在：创建新订单
        # =========================
        new_order = Order(
            email=data.get('email'),
            name=name,
            customer_name=data.get('customer_name'),
            member_name=data.get('member_name'),
            phone=phone,
            version=version,
        )

        db.session.add(new_order)
        db.session.commit()

        order_dict = OrderService.to_dict(new_order)

        return jsonify({
            'success': True,
            'message': '订单已创建',
            'order': order_dict,
            'duplicated': False
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

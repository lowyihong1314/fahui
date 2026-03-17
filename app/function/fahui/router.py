from flask import Blueprint, jsonify, request

from app.function.fahui.service import FahuiService

fahui_router_bp = Blueprint('fahui_router', __name__)

@fahui_router_bp.route("/search", methods=["GET"])
def search():

    # ===== 参数读取 =====
    version = request.args.get("version", type=str)
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
    try:
        result = FahuiService.search_orders(version=version, value=value, page=page, per_page=per_page)
    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

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
    order_data = FahuiService.get_order_detail(order_id)
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

@fahui_router_bp.route("/get_orders_by_phone", methods=["GET"])
def get_orders_by_phone():
    phone = request.args.get("phone", default="", type=str)
    payload, status_code = FahuiService.get_orders_by_phone(phone)
    return jsonify(payload), status_code

@fahui_router_bp.route('/new_customer', methods=['POST'])
def new_customer():
    data = request.get_json() or {}

    try:
        return jsonify(FahuiService.create_customer(data))

    except Exception as e:
        from app.extensions import db

        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

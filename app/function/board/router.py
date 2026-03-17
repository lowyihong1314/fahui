from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required,current_user
from app.models import Order, PrintPDF
from app.extensions import db
from app.function.common import verification_required

from app.function.board.command_service import BoardCommandService
from app.function.board.query_service import BoardQueryService

board_router_bp = Blueprint('board_router', __name__)

@board_router_bp.route("/get_pdf_data/<int:pdf_id>", methods=["GET"])
def get_pdf_data(pdf_id):
    payload, status_code = BoardQueryService.get_pdf_data(pdf_id)
    return jsonify(payload), status_code

@board_router_bp.route("/delete_board/<int:board_data_id>", methods=["DELETE"])
def delete_board(board_data_id):
    try:
        payload, status_code = BoardRouterService.delete_board(board_data_id)
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@board_router_bp.route("/list_all", methods=["GET"])
def list_all_boards():
    return jsonify(BoardQueryService.list_all_boards())

@board_router_bp.route("/insert_pdf", methods=["POST"])
def insert_pdf():
    try:
        payload, status_code = BoardCommandService.insert_pdf(request.get_json() or {})
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@board_router_bp.route("/add_pdf", methods=["POST"])
def add_pdf():
    try:
        payload, status_code = BoardCommandService.add_pdf(request.get_json() or {})
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@board_router_bp.route('/clear_print_pdf', methods=['GET'])
def clear_print_pdf():
    try:
        payload, status_code = BoardCommandService.clear_print_pdf()
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    
@board_router_bp.route('/get_all_print_data', methods=['GET'])
def get_all_print_data():
    return jsonify(BoardQueryService.get_all_print_data()), 200

@board_router_bp.route('/get_version_list', methods=['GET'])
@login_required
def get_version_list():
    return jsonify(BoardQueryService.get_version_list())

@board_router_bp.route('/get_orders_data', methods=['GET'])
@login_required
def get_order_data():
    # 获取 version 参数（默认为 '2024_YLP'）
    version = request.args.get('version', '2024_YLP')  # 如果没有传 version 参数，使用默认值 '2024_YLP'
    
    # 获取所有指定版本的订单数据
    orders = Order.get_order_data_by_version(version)
    
    # 返回 JSON 格式的订单数据
    return jsonify(orders)

@board_router_bp.route('/update_customer/<int:order_id>', methods=['POST'])
@verification_required(order_id_arg_name='order_id')
def update_customer(order_id):
    try:
        payload, status_code = BoardCommandService.update_customer(
            order_id,
            request.get_json() or {},
            current_user.is_authenticated,
        )
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@board_router_bp.route('/get_order_detail', methods=['GET'])
def get_order_detail():
    payload, status_code = BoardQueryService.get_order_detail(
        request.args.get('id', type=int)
    )
    return jsonify(payload), status_code

@board_router_bp.route('/check_duplicate_owner_fields', methods=['GET'])
def check_duplicate_owner_fields():
    return jsonify(BoardQueryService.check_duplicate_owner_fields())

@board_router_bp.route('/fahui_search_emgine', methods=['POST'])
def fahui_search_emgine():
    payload = BoardQueryService.search_orders(
        (request.get_json() or {}).get("keyword"),
        current_user.is_authenticated,
    )
    return jsonify(payload)

@board_router_bp.route('/add_paiwei/<int:order_id>', methods=['POST'])
@verification_required(order_id_arg_name='order_id')
def add_paiwei(order_id):
    try:
        payload, status_code = BoardCommandService.add_paiwei(
            order_id,
            request.get_json() or {},
        )
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@board_router_bp.route('/delete_item/<int:item_id>/<int:order_id>', methods=['DELETE'])
@verification_required(order_id_arg_name='order_id')
def delete_item(item_id,order_id):
    try:
        payload, status_code = BoardCommandService.delete_item(item_id)
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@board_router_bp.route('/delete_orders', methods=['POST'])
@login_required
def delete_orders():
    try:
        payload, status_code = BoardCommandService.delete_orders(request.get_json() or {})
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@board_router_bp.route('/copy_old_data', methods=['POST'])
def copy_old_data():
    try:
        payload, status_code = BoardCommandService.copy_old_data(request.get_json() or {})
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@board_router_bp.route('/update_item_form_value', methods=['POST'])
def update_item_form_value():
    try:
        payload, status_code = BoardCommandService.update_item_form_value(
            request.get_json() or {}
        )
        return jsonify(payload), status_code
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

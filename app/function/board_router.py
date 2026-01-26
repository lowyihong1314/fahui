from datetime import datetime
from flask import send_file, current_app, Blueprint, jsonify,request
from flask_login import login_required,current_user
from app.models.fahui import Order,ItemFormData,OrderItem,PrintPDF,PDFPageData,BoardData,BoardHeader
from app.extensions import db
from app.function.config import verification_required
from sqlalchemy import text

from app.services.order_service import OrderService
from app.services.board_service import BoardService

board_router_bp = Blueprint('board_router', __name__)

@board_router_bp.route("/get_pdf_data/<int:pdf_id>", methods=["GET"])
def get_pdf_data(pdf_id):
    pdf = PrintPDF.query.get(pdf_id)
    if not pdf:
        return jsonify({"status": "error", "message": f"PrintPDF {pdf_id} 不存在"}), 404

    return jsonify({
        "status": "success",
        "data": pdf.to_dict()
    })

@board_router_bp.route("/delete_board/<int:board_data_id>", methods=["DELETE"])
def delete_board(board_data_id):
    try:
        board = BoardData.query.get(board_data_id)
        if not board:
            return jsonify({"status": "error", "message": f"BoardData {board_data_id} not found"}), 404

        db.session.delete(board)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": f"BoardData {board_data_id} deleted successfully",
            "all_board": BoardService.get_all_boards_with_orders()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@board_router_bp.route("/list_all", methods=["GET"])
def list_all_boards():
    return jsonify({"all_board": BoardService.get_all_boards_with_orders()})

@board_router_bp.route("/insert_pdf", methods=["POST"])
def insert_pdf():
    data = request.get_json()
    board_id = data.get("board_id")
    pdf_id = data.get("pdf_id")
    location = data.get("location")

    if not board_id or not pdf_id or not location:
        return jsonify({"error": "board_id, pdf_id, location 都不能为空"}), 400

    try:
        board_id = int(board_id)
        pdf_id = int(pdf_id)
        location = int(location)
    except ValueError:
        return jsonify({"error": "参数必须是整数"}), 400

    # 找到目标 pdf
    entry = BoardData.query.filter_by(print_pdf_id=pdf_id, board_id=board_id).first()
    if not entry:
        return jsonify({"error": f"pdf_id={pdf_id} 不存在于 board_id={board_id}"}), 400

    old_location = entry.location

    if old_location == location:
        return jsonify({"success": True, "message": "位置未改变"})

    # 向前移动 / 向后移动
    if old_location < location:
        # 往后拖动：区间内 -1
        BoardData.query.filter(
            BoardData.board_id == board_id,
            BoardData.location > old_location,
            BoardData.location <= location
        ).update({BoardData.location: BoardData.location - 1}, synchronize_session=False)
    else:
        # 往前拖动：区间内 +1
        BoardData.query.filter(
            BoardData.board_id == board_id,
            BoardData.location >= location,
            BoardData.location < old_location
        ).update({BoardData.location: BoardData.location + 1}, synchronize_session=False)

    # 设置新位置
    entry.location = location

    db.session.commit()

    return jsonify({
        "success": True,
        "board_id": board_id,
        "pdf_id": pdf_id,
        "location": location,
        "all_board": BoardService.get_all_boards_with_orders()
    })

@board_router_bp.route("/add_pdf", methods=["POST"])
def add_pdf():
    data = request.get_json()
    board_id = data.get("board_id")
    pdf_id = data.get("pdf_id")
    board_name = data.get("board_name")
    board_width = data.get("board_width")
    board_height = data.get("board_height")

    # ⚡ 转换宽高：空字符串 -> None，数字字符串 -> int
    def parse_int(val):
        if val in ["", None]:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    board_width = parse_int(board_width)
    board_height = parse_int(board_height)
    
    if not board_id:
        return jsonify({"error": "board_id 不能为空"}), 400

    # ⚡ 转换 pdf_id
    if pdf_id in ["none", "", None]:
        pdf_id = None
    else:
        try:
            pdf_id = int(pdf_id)
        except ValueError:
            return jsonify({"error": "pdf_id 必须是整数或 none"}), 400

    # 查找 PDF 是否存在
    if pdf_id:
        pdf = PrintPDF.query.get(pdf_id)
        if not pdf:
            return jsonify({"error": f"print_pdf_id={pdf_id} 不存在"}), 400

        # ⚡ 检查是否已经被绑定过
        existing = BoardData.query.filter_by(print_pdf_id=pdf_id).first()
        if existing:
            return jsonify({"error": f"pdf_id={pdf_id} 已经绑定在 board_id={existing.board_id} 上"}), 400

    # 查找或创建 BoardHeader
    header = BoardHeader.query.get(board_id)
    if not header:
        if not board_name:  
            board_name = f"board_{board_id}"
        header = BoardHeader(
            id=board_id,
            board_name=board_name,
            board_width=board_width,
            board_height=board_height
        )
        db.session.add(header)
        db.session.flush()
    else:
        # 如果传了宽高就更新
        if board_width is not None:
            header.board_width = board_width
        if board_height is not None:
            header.board_height = board_height
        if board_name:  # 允许更新名字
            header.board_name = board_name

    board_entry = None  # 默认不生成 BoardData

    # ⚡ 只有 pdf_id 存在时才操作 BoardData
    if pdf_id:
        board_entry = BoardData.query.filter_by(board_id=header.id, print_pdf_id=None).first()

        if board_entry:
            board_entry.print_pdf_id = pdf_id
        else:
            # ✅ 获取该 board_id 下最大的 location
            last_location = db.session.query(db.func.max(BoardData.location)) \
                                    .filter_by(board_id=header.id).scalar() or 0

            board_entry = BoardData(
                board_id=header.id,
                print_pdf_id=pdf_id,
                location=last_location + 1   # ⚡ 自动递增
            )
            db.session.add(board_entry)


    db.session.commit()

    payload = {
        "side_id": board_entry.id if board_entry else None,
        "pdf_id": pdf_id,
        "pdf_data": [],
        "all_board": BoardService.get_all_boards_with_orders()
    }

    return jsonify(payload)


@board_router_bp.route('/clear_print_pdf', methods=['GET'])
def clear_print_pdf():
    try:
        # 先清空子表
        db.session.query(PDFPageData).delete()
        db.session.commit()

        # 再清空父表
        db.session.query(PrintPDF).delete()
        db.session.commit()

        # 重置自增 ID
        db.session.execute(text("ALTER TABLE pdf_page_data AUTO_INCREMENT = 1"))
        db.session.execute(text("ALTER TABLE print_pdf AUTO_INCREMENT = 1"))
        db.session.commit()

        return jsonify({"success": True, "message": "Tables cleared and IDs reset"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    
@board_router_bp.route('/get_all_print_data', methods=['GET'])
def get_all_print_data():
    records = PrintPDF.query.order_by(PrintPDF.created_at.desc()).all()
    return jsonify([record.to_dict() for record in records]), 200

@board_router_bp.route('/get_version_list', methods=['GET'])
@login_required
def get_version_list():
    # 从订单表中去重获取所有 version
    versions = db.session.query(Order.version).distinct().all()

    # 格式化为列表（去掉 tuple）
    version_list = [v[0] for v in versions if v[0] is not None]

    return jsonify(version_list)

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
    data = request.get_json()
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404

    # 更新 customer_name 和 email（不限制）
    order.customer_name = data.get('customer_name', order.customer_name)
    order.email = data.get('email', order.email)

    # 更新 phone 只有当新手机号与旧手机号不同时才检查权限
    new_phone = data.get('phone')
    if new_phone and new_phone != order.phone:
        if current_user.is_authenticated:
            order.phone = new_phone
        else:
            return jsonify({'success': False, 'message': '未登录用户无法修改手机号'}), 403

    db.session.commit()
    return jsonify({'success': True, 'message': 'Customer info updated'})


@board_router_bp.route('/get_order_detail', methods=['GET'])
def get_order_detail():
    order_id = request.args.get('id', type=int)
    
    if not order_id:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    order = Order.query.get(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    order_detail = OrderService.to_all_detail(order)

    return jsonify(order_detail)

@board_router_bp.route('/check_duplicate_owner_fields', methods=['GET'])
def check_duplicate_owner_fields():
    from sqlalchemy import func
    # 找出所有 item_id 在 field_name='owner' 出现次数 > 1 的 item_id
    subquery = (
        db.session.query(
            ItemFormData.item_id,
            func.count(ItemFormData.id).label('owner_count')
        )
        .filter(ItemFormData.field_name == 'owner')
        .group_by(ItemFormData.item_id)
        .having(func.count(ItemFormData.id) > 1)
        .subquery()
    )

    # 根据重复的 item_id 查找对应的 order_id，去重
    order_ids = (
        db.session.query(OrderItem.order_id)
        .join(subquery, OrderItem.id == subquery.c.item_id)
        .distinct()
        .all()
    )

    # 提取 order_id 列表
    order_id_list = [oid[0] for oid in order_ids]

    return jsonify(order_id_list)

@board_router_bp.route('/fahui_search_emgine', methods=['POST'])
def fahui_search_emgine():
    from sqlalchemy import or_
    data = request.get_json()
    keyword = (data.get("keyword") or "").strip().lower()

    if not keyword:
        return jsonify({"success": True, "results": []})

    is_number = keyword.isdigit()
    orders = []

    if is_number:
        # ✅ 1. 先按 order_id 精确查
        order = Order.query.filter_by(id=int(keyword)).first()
        if order:
            orders = [order]

        # ✅ 2. 没有则按 order_item_id 查
        if not orders:
            order_item = OrderItem.query.filter_by(id=int(keyword)).first()
            if order_item:
                orders = [order_item.order]

        # ✅ 3. 再按 phone 模糊查
        if not orders:
            orders = Order.query.filter(Order.phone.like(f"%{keyword}%")) \
                                .order_by(Order.created_at.desc()).limit(5).all()

    else:
        # 非数字走原来的名字类模糊搜索
        orders = Order.query.filter(
            or_(
                Order.customer_name.ilike(f"%{keyword}%"),
                Order.name.ilike(f"%{keyword}%"),
                Order.member_name.ilike(f"%{keyword}%")
            )
        ).order_by(Order.created_at.desc()).limit(5).all()

    # ✅ 主表查不到 → 去 item 数据中查
    if not orders:
        matched_item_ids = db.session.query(ItemFormData.item_id) \
            .filter(ItemFormData.field_value.ilike(f"%{keyword}%")) \
            .limit(10).all()

        item_ids = [item_id for (item_id,) in matched_item_ids]

        if item_ids:
            order_ids = db.session.query(OrderItem.order_id) \
                .filter(OrderItem.id.in_(item_ids)).limit(10).all()

            order_ids = [oid for (oid,) in order_ids]

            if order_ids:
                flat_order_ids = [oid for (oid,) in order_ids]
                top_ids = sorted(flat_order_ids, reverse=True)[:5]

                orders = Order.query.filter(Order.id.in_(top_ids)).all()
                orders.sort(key=lambda o: top_ids.index(o.id))

    # 🚨 在这里过滤掉 DELETE 且未登录的
    results = []
    for order in orders:
        if order.version == "DELETE" and (not current_user or not current_user.is_authenticated):
            continue
        results.append(OrderService.to_dict(order))

    return jsonify({
        "success": True,
        "results": results
    })

@board_router_bp.route('/add_paiwei/<int:order_id>', methods=['POST'])
@verification_required(order_id_arg_name='order_id')
def add_paiwei(order_id):
    data = request.get_json()
    try:
        # 检查至少提供 owner 或 deceased
        owner = data.get('owner')
        deceased = data.get('deceased')
        code = data.get('form-group')

        has_valid_owner = isinstance(owner, list) and any((name or '').strip() for name in owner)
        has_valid_deceased = (
            (isinstance(deceased, str) and deceased.strip()) or
            (isinstance(deceased, list) and any((d or '').strip() for d in deceased))
        )

        if isinstance(owner, list):
            for name in owner:
                if name and len(name.strip()) > 50:
                    return jsonify({
                        'success': False,
                        'message': f"施主姓名“{name}”不能超过 5 个字"
                    }), 400
                
        if code in ['A2', 'B2']:
            if not (has_valid_owner and has_valid_deceased):
                return jsonify({'success': False, 'message': 'A2/B2 表单必须同时填写 owner 和 deceased'}), 400
        elif code == 'D1':
            # ⚡ D1 不需要 owner / deceased
            pass
        elif not (has_valid_owner or has_valid_deceased):
            return jsonify({'success': False, 'message': '必须填写 owner 或 deceased 至少一项'}), 400
        # 解析核心字段
        
        item_name = data.get('item_name')
        price = data.get('price')
        if price is None:
            price = get_item_price(code)

        # 1. 写入 OrderItem
        order_item = OrderItem(
            order_id=order_id,
            code=code,
            item_name=item_name,
            price=price
        )
        db.session.add(order_item)
        db.session.commit()  # 获取 order_item.id

        # 2. 循环写入 ItemFormData
        item_id = order_item.id
        skip_keys = {'form_code', 'form-group', 'item_name', 'price'}

        for key, value in data.items():
            if key in skip_keys:
                continue

            if isinstance(value, list):
                for v in value:
                    if v is None or str(v).strip() == "":
                        continue
                    form_data = ItemFormData(
                        item_id=item_id,
                        field_name=key,
                        field_value=str(v).strip()
                    )
                    db.session.add(form_data)
            else:
                if value is None or str(value).strip() == "":
                    continue
                form_data = ItemFormData(
                    item_id=item_id,
                    field_name=key,
                    field_value=str(value).strip()
                )
                db.session.add(form_data)

        db.session.commit()

        return jsonify({'success': True, 'message': '已保存', 'item_id': item_id})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

def get_item_price(code):
    price_list = [
        {'A1': 100},
        {'A2': 100},
        {'A3': 100},
        {'B1': 35},
        {'B2': 35},
        {'B3': 35},
        {'C': 15},
        {'D1': 50}
    ]

    for item in price_list:
        if code in item:
            return item[code]

    # 如果没找到，默认返回 0 或抛错
    return 0  # 或者 raise ValueError(f"未找到价格: {code}")

@board_router_bp.route('/delete_item/<int:item_id>/<int:order_id>', methods=['DELETE'])
@verification_required(order_id_arg_name='order_id')
def delete_item(item_id,order_id):
    try:
        # 查找 OrderItem
        item = OrderItem.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'message': '未找到该订单项'}), 404

        # 删除关联的 ItemFormData
        ItemFormData.query.filter_by(item_id=item_id).delete()

        # 删除 OrderItem 本身
        db.session.delete(item)
        db.session.commit()

        return jsonify({'success': True, 'message': '删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@board_router_bp.route('/delete_orders', methods=['POST'])
@login_required
def delete_orders():
    try:
        data = request.get_json()
        orders = data.get('data', [])

        if not orders:
            return jsonify({'status': 'error', 'message': '未提供任何订单数据'}), 400

        order_ids = [order['id'] for order in orders if 'id' in order]

        if not order_ids:
            return jsonify({'status': 'error', 'message': '数据中没有包含订单 ID'}), 400

        # 查询所有待处理的订单
        orders_to_delete = Order.query.filter(Order.id.in_(order_ids)).all()

        deleted_count = 0
        marked_count = 0

        for order in orders_to_delete:
            if str(order.version) == "DELETE":
                # 已经标记过 -> 物理删除
                db.session.delete(order)
                deleted_count += 1
            else:
                # 第一次删除 -> 逻辑删除（标记）
                order.version = "DELETE"
                marked_count += 1

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': f'标记删除 {marked_count} 个订单，物理删除 {deleted_count} 个订单',
            'marked': marked_count,
            'deleted': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@board_router_bp.route('/copy_old_data', methods=['POST'])
def copy_old_data():
    data = request.get_json()
    order_id = data.get('order_id')
    new_version = '2025_YLP'

    if not order_id or new_version is None:
        return jsonify({"error": "order_id and new_version are required"}), 400

    # 获取原始订单
    old_order = Order.query.get(order_id)
    if not old_order:
        return jsonify({"error": f"Order with id {order_id} not found"}), 404

    # 🚫 如果旧订单已经是这个版本，禁止复制
    if old_order.version == new_version:
        return jsonify({"error": f"Order {order_id} already has version {new_version}, cannot copy again."}), 400

    # ✅ 复制 Order
    new_order = Order(
        name=old_order.name,
        email=old_order.email,
        customer_name=old_order.customer_name,
        member_name=old_order.member_name,
        phone=old_order.phone,
        created_at=datetime.utcnow(),
        version=new_version
    )
    db.session.add(new_order)
    db.session.flush()  # 获取 new_order.id

    # ✅ 复制 OrderItem
    old_items = OrderItem.query.filter_by(order_id=old_order.id).all()
    item_id_map = {}

    for old_item in old_items:
        new_item = OrderItem(
            order_id=new_order.id,
            code=old_item.code,
            item_name=old_item.item_name,
            price=old_item.price
        )
        db.session.add(new_item)
        db.session.flush()
        item_id_map[old_item.id] = new_item.id

        # ✅ 复制 ItemFormData
        form_data_list = ItemFormData.query.filter_by(item_id=old_item.id).all()
        for old_data in form_data_list:
            new_data = ItemFormData(
                item_id=new_item.id,
                field_name=old_data.field_name,
                field_value=old_data.field_value
            )
            db.session.add(new_data)

    db.session.commit()

    return jsonify({
        "message": "Order copied successfully",
        "new_order_id": new_order.id
    }), 201


@board_router_bp.route('/update_item_form_value', methods=['POST'])
def update_item_form_value():
    data = request.get_json()
    item_form_id = data.get('id')
    new_value = data.get('value')

    if not item_form_id or new_value is None:
        return jsonify({"success": False, "message": "缺少参数"}), 400

    item_form = ItemFormData.query.get(item_form_id)
    if not item_form:
        return jsonify({"success": False, "message": "未找到数据"}), 404

    item_form.field_value = new_value
    db.session.commit()

    return jsonify({"success": True})


from flask import jsonify, request
from flask_login import login_required

from app.function.print_paiwei.blueprint import print_paiwei_bp
from app.function.print_paiwei.points import load_point_json, save_point_json


@print_paiwei_bp.route("/get_point_json", methods=["GET"])
@login_required
def get_point_json():
    return jsonify(load_point_json())


@print_paiwei_bp.route("/update_point_json", methods=["POST"])
@login_required
def update_point_json():
    try:
        save_point_json(request.get_json())
        return jsonify({"success": True, "message": "point.json 更新成功"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

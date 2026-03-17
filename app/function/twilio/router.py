from flask import Blueprint, jsonify, request, session
from flask_login import current_user
from _token import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, VERIFY_SERVICE_SID
from app.function.common import redis_client
from app.function.twilio.service import (
    RATE_LIMIT,
    RATE_LIMIT_TTL,
    build_client,
    check_rate_limit,
    get_remote_ip,
    mark_verified_phone,
)
from app.models import Order  # 确保你导入了 Order 模型

twilio_bp = Blueprint('twilio', __name__)
client = build_client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@twilio_bp.route('/send_otp', methods=['POST'])
def send_otp():
    data = request.get_json(silent=True) or {}
    order_id = request.form.get('order_id') or data.get('order_id')
    phone = request.form.get('phone') or data.get('phone')
    ip = get_remote_ip()

    if order_id:
        order = Order.query.filter_by(id=order_id).first()
        if not order or not order.phone:
            return jsonify({"status": "fail", "message": "找不到对应手机号"}), 404
        phone = order.phone
    elif phone:
        order = Order.query.filter_by(phone=phone).first()
        if not order:
            return jsonify({"status": "fail", "message": "这个手机号下没有订单"}), 404
    else:
        return jsonify({"status": "fail", "message": "缺少 order_id 或 phone"}), 400

    if current_user.is_authenticated:
        mark_verified_phone(phone)
        session['phone'] = phone
        return jsonify({
            "status": "login_bypass",
            "message": "当前已登录，已跳过短信验证",
            "data": {"phone": phone}
        }), 200

    # ✅ 如果 session 中已有这个 phone，就直接返回
    if session.get('phone') == phone:
        return jsonify({
            "status": "cookie_true",
            "message": "已存在手机号 cookie，无需重复发送"
        }), 200

    ip_key = f"sms_send_attempts:{ip}"
    current_attempts = redis_client.get(ip_key)
    if current_attempts and int(current_attempts) >= RATE_LIMIT:
        return jsonify({
            "status": "fail",
            "message": "该 IP 请求验证码过于频繁，请 1 小时后再试"
        }), 429

    try:
        session['phone'] = phone

        client.verify.v2.services(VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel='sms'
        )

        redis_client.incr(ip_key)
        redis_client.expire(ip_key, RATE_LIMIT_TTL)

        return jsonify({
            "status": "success",
            "message": f"验证码已发送到你的手机"
        })

    except Exception as e:
        return jsonify({
            "status": "fail",
            "message": f"发送验证码失败: {str(e)}"
        }), 500

@twilio_bp.route('/verify', methods=['POST'])
def verify_otp():
    data = request.get_json(silent=True) or {}
    otp = data.get('otp')
    phone = data.get('phone') or session.get('phone')
    ip = get_remote_ip()

    if not otp or not phone:
        return jsonify({"status": "fail", "message": "验证码或手机号缺失"}), 400

    ip_key = f"verify_attempts:{ip}"
    ok, resp, code = check_rate_limit(ip_key)
    if not ok:
        return resp, code

    try:
        verification_check = client.verify.v2.services(VERIFY_SERVICE_SID).verification_checks.create(
            to=phone,
            code=otp
        )

        if verification_check.status == 'approved':
            mark_verified_phone(phone)
            return jsonify({
                "status": "success",
                "message": "验证码验证成功",
                "data": {"phone": phone}
            })
        else:
            return jsonify({"status": "fail", "message": "验证码错误或已过期"}), 401
    except Exception as e:
        return jsonify({"status": "fail", "message": f"验证码验证失败: {str(e)}"}), 500

@twilio_bp.route("/debug_session")
def debug_session():
    print("session phone:", repr(session.get('phone')))
    return jsonify({
        "session_phone": session.get("phone"),
        "all_session": dict(session)
    })

@twilio_bp.route('/test_send_otp', methods=['GET'])  # 改成 GET
def test_send_otp():
    order_id = request.args.get('order_id')  # 从 URL 参数获取

    if not order_id:
        return jsonify({"status": "fail", "message": "缺少 order_id"}), 400

    # 获取订单
    order = Order.query.filter_by(id=order_id).first()
    if not order or not order.phone:
        return jsonify({"status": "fail", "message": "找不到对应手机号"}), 404

    phone = order.phone

    # ✅ 如果已经登录，或者 session 中已有相同 phone，直接跳过发送
    if session.get('logged_in') is True or session.get('phone') == phone:
        return jsonify({
            "status": "cookie_true",
            "message": "已存在手机号 cookie 或已登录，无需重复发送"
        }), 200

    # 否则记录 session 并继续
    session['phone'] = phone

    return jsonify({
        "status": "success",
        "message": f"测试模式：验证码已“发送”到 {phone}"
    })


@twilio_bp.route('/test_verify', methods=['POST'])
def test_verify_otp():
    data = request.get_json(silent=True) or {}
    otp = data.get('otp')
    phone = session.get('phone')

    if not otp or not phone:
        return jsonify({"status": "fail", "message": "验证码或手机号缺失"}), 400

    if otp == "8888":
        mark_verified_phone(phone)
        return jsonify({
            "status": "success",
            "message": "测试验证成功",
            "data": {"phone": phone}
        })
    else:
        return jsonify({"status": "fail", "message": "测试模式：验证码错误"}), 401

@twilio_bp.route('/clear_phone_session', methods=['POST'])
def clear_phone_session():
    session.pop('phone', None)
    return jsonify({"status": "success", "message": "已清除手机号 session"})

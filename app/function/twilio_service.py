from flask import Flask, Blueprint, request, session, url_for, jsonify,render_template
from twilio.rest import Client
import os
from app.function.redis_client import redis_client
from app.models.fahui import Order  # 确保你导入了 Order 模型
from app.extensions import db
from _token import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, VERIFY_SERVICE_SID

twilio_bp = Blueprint('twilio', __name__)
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

RATE_LIMIT = 500000        # 每小时最多验证次数
RATE_LIMIT_TTL = 3600  # TTL 设置为 1 小时

def get_remote_ip():
    """获取用户真实 IP，支持代理情况"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr

@twilio_bp.route('/send_otp', methods=['POST'])
def send_otp():
    order_id = request.form.get('order_id') or request.json.get('order_id')
    ip = get_remote_ip()

    if not order_id:
        return jsonify({"status": "fail", "message": "缺少 order_id"}), 400

    # 获取 phone
    order = Order.query.filter_by(id=order_id).first()
    if not order or not order.phone:
        return jsonify({"status": "fail", "message": "找不到对应手机号"}), 404

    phone = order.phone

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


def get_order_phone(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order or not order.phone:
        return None

    formatted_phone = order.phone

    if formatted_phone and formatted_phone != order.phone:
        # 更新数据库中保存的手机号
        order.phone = formatted_phone
        try:
            db.session.commit()  # 你要确保 db 是你的 SQLAlchemy 实例
        except Exception as e:
            db.session.rollback()
            print(f"更新手机号失败: {e}")
            return None

    return formatted_phone

def check_rate_limit(ip_key):
    """检查并增加限流计数"""
    try:
        current_attempts = redis_client.get(ip_key)
        if current_attempts and int(current_attempts) >= RATE_LIMIT:
            return False, jsonify({
                "status": "fail",
                "message": "该 IP 提交次数已达上限，请 1 小时后再试"
            }), 429

        pipe = redis_client.pipeline()
        pipe.incr(ip_key)
        pipe.ttl(ip_key)
        count, ttl = pipe.execute()
        if ttl == -1:
            redis_client.expire(ip_key, RATE_LIMIT_TTL)

        return True, None, None
    except Exception as e:
        return False, jsonify({
            "status": "fail",
            "message": f"限流检查出错: {str(e)}"
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
            verified_phones = session.get('verified_phones', [])
            if phone not in verified_phones:
                verified_phones.append(phone)
                session['verified_phones'] = verified_phones

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
        verified_phones = session.get('verified_phones', [])
        if phone not in verified_phones:
            verified_phones.append(phone)
            session['verified_phones'] = verified_phones

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

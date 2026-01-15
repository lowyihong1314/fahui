from flask import Flask, Blueprint, request, session, url_for, jsonify,render_template
from twilio.rest import Client
import os
from function.redis_client import redis_client
from models.fahui import Order  # 确保你导入了 Order 模型
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

@twilio_bp.route('/index/<int:order_id>', methods=['GET'])
def verification_page(order_id):
    # 从数据库获取订单
    order = Order.query.get(order_id)
    ip = get_remote_ip()
    return render_template(
        'verification_page.html',
        phone_number=order.phone,   # 从 Order 表取出
        order_id=order.id,
        ip=ip
    )

@twilio_bp.route('/', methods=['POST'])
def send_otp():
    order_id = request.form.get('order_id') or request.json.get('order_id')
    ip = get_remote_ip()
    #print(f"[DEBUG] 请求来自 IP: {ip}, 订单号: {order_id}")

    if not order_id:
        return jsonify({
            "status": "fail",
            "message": "订单号不能为空"
        }), 400

    # 从订单获取手机号
    phone = get_order_phone(order_id)
    #print(f"[DEBUG] 获取到手机号: {phone}")

    if not phone:
        return jsonify({
            "status": "fail",
            "message": "订单对应手机号不存在"
        }), 404

    ip_key = f"sms_send_attempts:{ip}"

    # 限流检查
    try:
        current_attempts = redis_client.get(ip_key)
        #print(f"[DEBUG] 当前 IP 尝试次数: {current_attempts}")
        if current_attempts and int(current_attempts) >= RATE_LIMIT:
            return jsonify({
                "status": "fail",
                "message": "该 IP 请求验证码过于频繁，请 1 小时后再试"
            }), 429
    except Exception as e:
        #print(f"[ERROR] 限流检查异常: {str(e)}")
        return jsonify({
            "status": "fail",
            "message": f"限流检查失败: {str(e)}"
        }), 500

    try:
        # 打印环境变量相关信息
        #print(f"[DEBUG] TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}")
        #print(f"[DEBUG] VERIFY_SERVICE_SID: {VERIFY_SERVICE_SID}")
        #print(f"[DEBUG] 使用的 client 对象: {client}")

        # 保存手机号和订单号到 session
        session['phone'] = phone
        session['order_id'] = order_id
        #print(f"[DEBUG] Session 已保存: phone={phone}, order_id={order_id}")

        # 发送验证码
        #print(f"[DEBUG] 即将调用 Twilio Verify API, 目标手机号: {phone}")
        verification = client.verify.v2.services(VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel='sms'
        )
        #print(f"[DEBUG] Twilio 返回 verification 对象: {verification}")

        # 累计尝试次数
        redis_client.incr(ip_key)
        redis_client.expire(ip_key, RATE_LIMIT_TTL)
        #print(f"[DEBUG] Redis 限流计数已更新: {ip_key}")

        return jsonify({
            "status": "success",
            "message": f"验证码已发送到 {phone}",
            "data": {
                "next_url": f"/twilio/index/{phone}/{order_id}"
            }
        })

    except Exception as e:
        #print(f"[ERROR] 发送验证码失败: {str(e)}")
        return jsonify({
            "status": "fail",
            "message": f"发送验证码失败: {str(e)}"
        }), 500


def get_order_phone(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order or not order.phone:
        return None

    formatted_phone = format_phone_number(order.phone)

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

import re

def format_phone_number(raw_phone: str) -> str | None:
    """
    格式化手机号，统一转成 +60 开头的国际格式
    - +6011xxxxxx  -> 保持不变
    - 6011xxxxxx   -> 转成 +6011xxxxxx
    - 011xxxxxxx   -> 转成 +6011xxxxxxx
    - 1xxxxxxxx    -> 转成 +601xxxxxxxx
    其他情况返回 None
    """
    if not raw_phone:
        return None

    # 去掉空格、连字符、括号等，但保留开头的 +
    phone = re.sub(r'[^\d+]', '', raw_phone).strip()

    if phone.startswith('+60'):
        return phone
    elif phone.startswith('60'):
        return '+' + phone
    elif phone.startswith('0'):
        return '+60' + phone[1:]
    elif phone.startswith('1'):
        return '+60' + phone
    else:
        return None


def mark_verified(order_id, phone):
    """保存验证通过的状态到 session"""
    session['logged_in'] = True
    verified_phones = session.get('verified_phones', [])
    verified_orders = session.get('verified_orders', {})
    if phone not in verified_phones:
        verified_phones.append(phone)
        session['verified_phones'] = verified_phones
    verified_orders[str(order_id)] = phone
    session['verified_orders'] = verified_orders


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
    order_id = session.get('order_id') or data.get('order_id')
    ip = get_remote_ip()

    if not otp or not order_id:
        return jsonify({"status": "fail", "message": "验证码或订单号缺失"}), 400

    phone = get_order_phone(order_id)
    if not phone:
        return jsonify({"status": "fail", "message": "订单对应手机号不存在"}), 404

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
            mark_verified(order_id, phone)
            return jsonify({
                "status": "success",
                "message": "验证码验证成功",
                "data": {"phone": phone}
            })
        else:
            return jsonify({"status": "fail", "message": "验证码错误或已过期"}), 401
    except Exception as e:
        return jsonify({"status": "fail", "message": f"验证码验证失败: {str(e)}"}), 500


@twilio_bp.route('/submit_secret_code', methods=['POST'])
def submit_secret_code():
    data = request.get_json(silent=True) or {}
    secret_code = data.get('secret_code')
    order_id = data.get('order_id')
    ip = get_remote_ip()

    if not secret_code or not order_id:
        return jsonify({"status": "fail", "message": "密钥或订单号缺失"}), 400

    phone = get_order_phone(order_id)
    if not phone:
        return jsonify({"status": "fail", "message": "订单对应手机号不存在"}), 404

    ip_key = f"submit_secret_code_attempts:{ip}"
    ok, resp, code = check_rate_limit(ip_key)
    if not ok:
        return resp, code

    try:
        expected_code = str(int(order_id) + 1031)
        if str(secret_code) == expected_code:
            mark_verified(order_id, phone)
            return jsonify({
                "status": "success",
                "message": "密钥验证成功",
                "data": {"phone": phone}
            })
        else:
            return jsonify({"status": "fail", "message": "密钥错误"}), 401
    except Exception as e:
        return jsonify({"status": "fail", "message": f"密钥验证失败: {str(e)}"}), 500


@twilio_bp.route('/welcome', methods=['GET'])
def welcome():
    if session.get('logged_in'):
        return jsonify({
            "status": "success",
            "message": "欢迎访问，您已成功登录",
            "data": {
                "phone": session.get('phone')
            }
        })
    else:
        return jsonify({
            "status": "fail",
            "message": "未登录，请先进行手机号验证",
            "data": {
                "next_url": url_for('twilio.send_otp')
            }
        }), 401

@twilio_bp.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return jsonify({
        "status": "success",
        "message": "已退出登录"
    })

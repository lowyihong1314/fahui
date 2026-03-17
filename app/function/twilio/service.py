from flask import jsonify, request, session
from twilio.rest import Client

from app.extensions import db
from app.function.common import redis_client
from app.models import Order


RATE_LIMIT = 500000
RATE_LIMIT_TTL = 3600


def build_client(account_sid: str, auth_token: str):
    return Client(account_sid, auth_token)


def get_remote_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers["X-Forwarded-For"].split(",")[0].strip()
    return request.remote_addr


def get_order_phone(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order or not order.phone:
        return None

    formatted_phone = order.phone
    if formatted_phone and formatted_phone != order.phone:
        order.phone = formatted_phone
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return None

    return formatted_phone


def check_rate_limit(ip_key):
    try:
        current_attempts = redis_client.get(ip_key)
        if current_attempts and int(current_attempts) >= RATE_LIMIT:
            return False, jsonify({
                "status": "fail",
                "message": "该 IP 提交次数已达上限，请 1 小时后再试",
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
            "message": f"限流检查出错: {str(e)}",
        }), 500


def mark_verified_phone(phone: str):
    verified_phones = session.get("verified_phones", [])
    if phone not in verified_phones:
        verified_phones.append(phone)
        session["verified_phones"] = verified_phones

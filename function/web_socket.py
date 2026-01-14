from flask import request
from flask_socketio import SocketIO, emit, join_room
from function.redis_client import redis_client
from models.user_data import User,Notification
from datetime import datetime
from models import db
from flask_login import current_user

socketio = SocketIO(cors_allowed_origins="*")

REDIS_ONLINE_KEY = 'online_users'  # 哈希名

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    user_id = data.get('user_id')
    if room and user_id:
        join_room(room)
        redis_client.hset(REDIS_ONLINE_KEY, user_id, request.sid)
        broadcast_online_users()

        # 获取客户端 IP
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
        else:
            ip = request.remote_addr
        
        print(f"User {user_id} joined room {room} from IP: {ip}")
        
@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    # 查找哪个 user_id 的 sid 匹配
    all_users = redis_client.hgetall(REDIS_ONLINE_KEY)
    user_to_remove = None
    for user_id, stored_sid in all_users.items():
        if stored_sid == sid:
            user_to_remove = user_id
            break
    if user_to_remove:
        redis_client.hdel(REDIS_ONLINE_KEY, user_to_remove)
        broadcast_online_users()

def broadcast_online_users():
    online_user_ids = redis_client.hkeys(REDIS_ONLINE_KEY)
    emit('online_users', online_user_ids, broadcast=True)

def push_Notification(to_department, href, message):
    # 查询所有部门列表中包含指定部门的用户
    users = User.query.filter(User.department.contains([to_department])).all()

    if not users:
        print(f'没有找到属于部门 "{to_department}" 的用户。')
        return

    notifications = []
    for user in users:
        notif = Notification(
            from_department=current_user.department[0] if current_user.department else None,
            from_user_id=current_user.id,
            from_username=current_user.username,
            user_id=user.id,
            username=user.username,
            href=href,
            message=message,
            is_read=False,
            create_at=datetime.utcnow()
        )
        notifications.append(notif)
        socketio.emit('notice', {'msg': message}, room=user.username)

    # 批量插入
    db.session.bulk_save_objects(notifications)
    db.session.commit()
    print(f'推送通知成功，发送给 {len(users)} 个用户。')
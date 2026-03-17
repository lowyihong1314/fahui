from flask import Flask, Blueprint,send_from_directory
from app.extensions import db, login_manager, socketio
from app.config import DevConfig, ProdConfig

from app.function.board import board_router_bp
from app.function.common import flask_path
from app.function.fahui import fahui_router_bp
from app.function.payment import payment_bp
from app.function.print_paiwei import print_paiwei_bp
from app.function.template import template_bp
from app.function.twilio import twilio_bp
from app.function.user_control import user_control_bp
import os


def create_app(env="dev"):
    app = Flask(
        __name__,
        template_folder=os.path.join(flask_path, "templates"),
        static_folder=os.path.join(flask_path, "static"),
    )

    if env == "prod":
        app.config.from_object(ProdConfig)
    else:
        app.config.from_object(DevConfig)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # ===== api root blueprint（一定要在函数里创建）=====
    api_root_bp = Blueprint("api_root", __name__)

    api_root_bp.register_blueprint(template_bp, url_prefix="/template")
    api_root_bp.register_blueprint(user_control_bp, url_prefix="/user_control")
    api_root_bp.register_blueprint(board_router_bp, url_prefix="/board_router")  # /api 本身
    api_root_bp.register_blueprint(print_paiwei_bp, url_prefix="/print_paiwei")
    api_root_bp.register_blueprint(payment_bp, url_prefix="/payment")
    api_root_bp.register_blueprint(twilio_bp, url_prefix="/twilio")
    api_root_bp.register_blueprint(fahui_router_bp, url_prefix="/fahui_router")

    app.register_blueprint(api_root_bp, url_prefix="/api")
    

    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(
            os.path.join(flask_path, "static"), "index.html"
        )
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(flask_path, 'static', 'images', 'logo'),
            'logo.png',
            mimetype='image/png'
        )

    return app

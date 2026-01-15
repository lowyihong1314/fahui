from flask import Flask,render_template
from app.extensions import db, login_manager
from app.config import DevConfig, ProdConfig

from function.template import template_bp
from function.user_control import user_control_bp
from function.print_paiwei import print_paiwei_bp
from function.payment_gateway import payment_bp
from function.api import api_bp
from function.twilio_service import twilio_bp
from function.config import flask_path
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

    # register blueprints
    app.register_blueprint(template_bp, url_prefix="/template")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(user_control_bp, url_prefix="/user_control")
    app.register_blueprint(print_paiwei_bp, url_prefix="/print_paiwei")
    app.register_blueprint(payment_bp, url_prefix="/payment")
    app.register_blueprint(twilio_bp, url_prefix="/twilio_service")

    @app.route("/")
    def index():
        return render_template('index.html')

    return app

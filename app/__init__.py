from flask import Flask, Blueprint, Response, send_from_directory
from app.extensions import db, login_manager, socketio
from app.config import DevConfig, ProdConfig

from app.function.board import board_router_bp
from app.function.common import flask_path
from app.function.fahui import fahui_router_bp
from app.function.payment import payment_bp
from app.function.print_paiwei import print_paiwei_bp
from app.function.twilio import twilio_bp
from app.function.user_control import user_control_bp
import json
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

    api_root_bp.register_blueprint(user_control_bp, url_prefix="/user_control")
    api_root_bp.register_blueprint(board_router_bp, url_prefix="/board_router")  # /api 本身
    api_root_bp.register_blueprint(print_paiwei_bp, url_prefix="/print_paiwei")
    api_root_bp.register_blueprint(payment_bp, url_prefix="/payment")
    api_root_bp.register_blueprint(twilio_bp, url_prefix="/twilio")
    api_root_bp.register_blueprint(fahui_router_bp, url_prefix="/fahui_router")

    app.register_blueprint(api_root_bp, url_prefix="/api")

    def get_vite_entry_assets():
        manifest_path = os.path.join(app.static_folder, "vite", "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as manifest_file:
                manifest = json.load(manifest_file)

            entry = manifest.get("src/init.js")
            if not entry:
                raise KeyError("Missing Vite manifest entry for src/init.js")

            css_files = entry.get("css", [])
            js_file = entry["file"]
            return {
                "js": f"/static/vite/{js_file}",
                "css": [f"/static/vite/{css_file}" for css_file in css_files],
            }

        return {
            "js": "/static/vite/init.js",
            "css": [],
        }

    @app.route("/", methods=["GET"])
    def index():
        assets = get_vite_entry_assets()
        css_tags = "\n".join(
            f'    <link rel="stylesheet" href="{css_path}" />'
            for css_path in assets["css"]
        )

        html = f"""<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <title>法会系统</title>
    <link
      rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css"
      crossorigin="anonymous"
    />
    <link rel="icon" href="/static/images/logo/logo.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {{
        margin: 0;
        padding: 0;
      }}
    </style>
{css_tags}
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="{assets["js"]}"></script>
  </body>
</html>
"""
        return Response(html, mimetype="text/html")

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(
            os.path.join(app.static_folder, "images", "logo"),
            "logo.png",
            mimetype="image/png",
        )

    return app

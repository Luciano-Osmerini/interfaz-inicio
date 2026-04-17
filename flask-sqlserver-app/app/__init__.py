from datetime import timedelta
import os

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .models import db
from .routes import bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER_PROCESOS'], exist_ok=True)

    db.init_app(app)

    @app.after_request
    def add_private_network_header(response):
        # Needed by modern browsers when an HTTPS page calls a local API.
        if request.headers.get('Access-Control-Request-Private-Network') == 'true':
            response.headers.set('Access-Control-Allow-Private-Network', 'true')
        return response

    CORS(
        app,
        supports_credentials=True,
        origins=(
            app.config['CORS_ORIGINS'] + (['null'] if app.config.get('ALLOW_NULL_ORIGIN') else [])
        ),
    )

    app.permanent_session_lifetime = timedelta(minutes=app.config['SESSION_TIMEOUT_MINUTES'])

    with app.app_context():
        db.create_all()

    app.register_blueprint(bp)
    return app
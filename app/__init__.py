from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config import Config
from app.extensions import db, jwt
from app.models import AgendaItem, Session, Track, User
from app.routes import register_blueprints


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(User, int(identity))

    @app.errorhandler(OperationalError)
    @app.errorhandler(ProgrammingError)
    def handle_db_error(error):
        return jsonify({"error": "Database connection error.", "details": str(error)}), 503

    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app

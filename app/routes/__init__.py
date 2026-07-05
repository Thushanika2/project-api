from app.routes.agenda_routes import agenda_bp
from app.routes.auth_routes import auth_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.session_routes import sessions_bp
from app.routes.track_routes import tracks_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(tracks_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(agenda_bp)
    app.register_blueprint(dashboard_bp)

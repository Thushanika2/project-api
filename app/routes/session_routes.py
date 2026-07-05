from flask import Blueprint, jsonify, request
from flask_jwt_extended import current_user

from app.controllers import session_controller as ctrl
from app.middleware import roles_required

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@sessions_bp.get("")
def list_sessions():
    result, status = ctrl.get_sessions()
    return jsonify(result), status


@sessions_bp.get("/export")
@roles_required("organizer")
def export_sessions():
    fmt = request.args.get("format", "csv").lower()
    if fmt == "pdf":
        return ctrl.export_sessions_pdf()
    return ctrl.export_sessions_csv()


@sessions_bp.get("/popularity")
@roles_required("organizer")
def popularity():
    result, status = ctrl.get_sessions_popularity()
    return jsonify(result), status


@sessions_bp.post("/import")
@roles_required("organizer")
def import_sessions():
    file = request.files.get("file")
    result, status = ctrl.import_sessions_csv(file, current_user.id)
    return jsonify(result), status


@sessions_bp.get("/<int:session_id>/pdf")
def session_pdf(session_id):
    result = ctrl.export_session_pdf(session_id)
    if not hasattr(result, "mimetype"):
        return jsonify(result[0]), result[1]
    return result


@sessions_bp.get("/<int:session_id>")
def get_session(session_id):
    result, status = ctrl.get_session(session_id)
    return jsonify(result), status


@sessions_bp.post("")
@roles_required("organizer")
def create_session():
    result, status = ctrl.create_session(request.get_json(silent=True) or {}, current_user.id)
    return jsonify(result), status


@sessions_bp.put("/<int:session_id>")
@roles_required("organizer")
def update_session(session_id):
    result, status = ctrl.update_session(session_id, request.get_json(silent=True) or {})
    return jsonify(result), status


@sessions_bp.delete("/<int:session_id>")
@roles_required("organizer")
def delete_session(session_id):
    result, status = ctrl.delete_session(session_id)
    return jsonify(result), status

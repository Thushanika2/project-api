from flask import Blueprint, jsonify, request

from app.controllers import track_controller as ctrl
from app.middleware import roles_required

tracks_bp = Blueprint("tracks", __name__, url_prefix="/api/tracks")


@tracks_bp.get("")
def list_tracks():
    result, status = ctrl.get_tracks()
    return jsonify(result), status


@tracks_bp.get("/export")
def export_tracks():
    fmt = request.args.get("format", "csv").lower()
    if fmt == "pdf":
        return ctrl.export_tracks_pdf()
    return ctrl.export_tracks_csv()


@tracks_bp.post("/import")
@roles_required("organizer")
def import_tracks():
    file = request.files.get("file")
    result, status = ctrl.import_tracks_csv(file)
    return jsonify(result), status


@tracks_bp.get("/<int:track_id>")
def get_track(track_id):
    result, status = ctrl.get_track(track_id)
    return jsonify(result), status


@tracks_bp.post("")
@roles_required("organizer")
def create_track():
    result, status = ctrl.create_track(request.get_json(silent=True) or {})
    return jsonify(result), status


@tracks_bp.put("/<int:track_id>")
@roles_required("organizer")
def update_track(track_id):
    result, status = ctrl.update_track(track_id, request.get_json(silent=True) or {})
    return jsonify(result), status


@tracks_bp.delete("/<int:track_id>")
@roles_required("organizer")
def delete_track(track_id):
    result, status = ctrl.delete_track(track_id)
    return jsonify(result), status

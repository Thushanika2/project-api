from flask import Blueprint, jsonify, request

from app.controllers import agenda_item_controller as ctrl
from app.middleware import roles_required

agenda_bp = Blueprint("agenda", __name__, url_prefix="/api/agenda")


@agenda_bp.get("")
@roles_required("attendee")
def list_agenda():
    result, status = ctrl.get_agenda()
    return jsonify(result), status


@agenda_bp.post("")
@roles_required("attendee")
def add_agenda_item():
    result, status = ctrl.create_agenda_item(request.get_json(silent=True) or {})
    return jsonify(result), status


@agenda_bp.get("/export")
@roles_required("attendee")
def export_agenda():
    return ctrl.export_agenda_csv()


@agenda_bp.get("/pdf")
@roles_required("attendee")
def export_agenda_pdf():
    return ctrl.export_agenda_pdf()


@agenda_bp.post("/import")
@roles_required("attendee")
def import_agenda():
    file = request.files.get("file")
    result, status = ctrl.import_agenda_csv(file)
    return jsonify(result), status


@agenda_bp.delete("/<int:agenda_item_id>")
@roles_required("attendee")
def delete_agenda_item(agenda_item_id):
    result, status = ctrl.delete_agenda_item(agenda_item_id)
    return jsonify(result), status

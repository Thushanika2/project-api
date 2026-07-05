from flask import Blueprint, jsonify

from app.controllers import dashboard_controller as ctrl
from flask_jwt_extended import jwt_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/me")


@dashboard_bp.get("/dashboard")
@jwt_required()
def dashboard():
    result, status = ctrl.get_dashboard()
    return jsonify(result), status


@dashboard_bp.get("/dashboard/pdf")
@jwt_required()
def dashboard_pdf():
    return ctrl.export_dashboard_pdf()

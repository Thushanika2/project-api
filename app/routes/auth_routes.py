from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.controllers import auth_controller as ctrl

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    result, status = ctrl.register_user(request.get_json(silent=True) or {})
    return jsonify(result), status


@auth_bp.post("/login")
def login():
    result, status = ctrl.login_user(request.get_json(silent=True) or {})
    return jsonify(result), status


@auth_bp.post("/logout")
@jwt_required()
def logout():
    result, status = ctrl.logout_user()
    return jsonify(result), status


@auth_bp.get("/profile")
@jwt_required()
def profile():
    result, status = ctrl.get_profile()
    return jsonify(result), status


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    result, status = ctrl.update_profile(request.get_json(silent=True) or {})
    return jsonify(result), status

from flask_jwt_extended import create_access_token, current_user

from app.extensions import db
from app.models.user_model import User


def _validate_user_payload(data, user_id=None):
    errors = []
    if not data:
        return ["Request body is required."]

    email = (data.get("email") or "").strip()
    full_name = (data.get("full_name") or "").strip()

    if not email:
        errors.append("Email is required.")
    if not full_name and user_id is None:
        errors.append("Full name is required.")

    if email:
        query = User.query.filter_by(email=email)
        if user_id:
            query = query.filter(User.id != user_id)
        if query.first():
            errors.append("Email already exists.")

    return errors


def register_user(data):
    errors = _validate_user_payload(data)
    password = (data.get("password") or "").strip()
    if not password:
        errors.append("Password is required.")
    if len(errors) > 0:
        return {"errors": errors}, 400

    role = (data.get("role") or "attendee").strip()
    if role not in ("organizer", "attendee"):
        role = "attendee"

    try:
        user = User(
            email=data["email"].strip(),
            full_name=data["full_name"].strip(),
            role=role,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id))
        return {
            "message": "Registration successful.",
            "access_token": token,
            "user": user.to_dict(),
        }, 201
    except Exception:
        db.session.rollback()
        raise


def login_user(data):
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return {"error": "Email and password are required."}, 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return {"error": "Invalid email or password."}, 401
    if not user.is_active:
        return {"error": "Account is inactive."}, 403

    token = create_access_token(identity=str(user.id))
    return {
        "message": "Login successful.",
        "access_token": token,
        "user": user.to_dict(),
    }, 200


def logout_user():
    return {"message": "Logged out successfully."}, 200


def get_profile():
    return {"user": current_user.to_dict()}, 200


def update_profile(data):
    errors = _validate_user_payload(data, user_id=current_user.id)
    if len(errors) > 0:
        return {"errors": errors}, 400

    try:
        if data.get("full_name"):
            current_user.full_name = data["full_name"].strip()
        if data.get("avatar_url") is not None:
            current_user.avatar_url = data["avatar_url"].strip() or None
        if data.get("password"):
            current_user.set_password(data["password"])
        db.session.commit()
        return {"message": "Profile updated.", "user": current_user.to_dict()}, 200
    except Exception:
        db.session.rollback()
        raise

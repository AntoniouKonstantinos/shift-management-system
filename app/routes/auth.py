from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token
from app import db, limiter
from app.models import Employee
from app.security import login_required, MIN_PASSWORD_LENGTH

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _login_failed(response):
    return response.status_code == 401


def _current_password_wrong(response):
    return response.status_code == 403


@bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute", deduct_when=_login_failed)
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    employee = Employee.query.filter(db.func.lower(Employee.email) == email).first()
    account = employee.account if employee else None

    if account is None or not employee.is_active or not account.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(account.id))
    return jsonify({"access_token": token, "user": _serialize_user(account)}), 200


@bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify(_serialize_user(g.current_account)), 200


@bp.route("/change-password", methods=["POST"])
@limiter.limit("5 per 15 minutes", deduct_when=_current_password_wrong)
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if (
        not isinstance(current_password, str) or not current_password
        or not isinstance(new_password, str) or not new_password
    ):
        return jsonify({"error": "Current password and new password are required"}), 400

    account = g.current_account

    if not account.check_password(current_password):
        return jsonify({"error": "Current password is incorrect"}), 403

    if len(new_password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"Password must be at least {MIN_PASSWORD_LENGTH} characters"}), 400

    if new_password == current_password:
        return jsonify({"error": "New password must be different from the current one"}), 400

    account.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password updated"}), 200


def _serialize_user(account):
    employee = account.employee
    return {
        "employee_id": employee.id,
        "full_name": employee.full_name,
        "email": employee.email,
        "role": employee.role.name,
        "access_level": account.access_level,
    }
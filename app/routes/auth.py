from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token
from app import db
from app.models import Employee
from app.security import login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/login", methods=["POST"])
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


def _serialize_user(account):
    employee = account.employee
    return {
        "employee_id": employee.id,
        "full_name": employee.full_name,
        "email": employee.email,
        "role": employee.role.name,
        "access_level": account.access_level,
    }
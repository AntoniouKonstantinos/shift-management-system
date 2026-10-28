from flask import Blueprint, request, jsonify, g
from app import db
from app.models import Employee, Role, UserAccount, ACCESS_MANAGER, ACCESS_EMPLOYEE
from app.security import manager_required, MIN_PASSWORD_LENGTH

bp = Blueprint("employees", __name__, url_prefix="/api/employees")

VALID_ACCESS_LEVELS = {ACCESS_MANAGER, ACCESS_EMPLOYEE}


@bp.route("", methods=["GET"])
@manager_required
def list_employees():
    employees = Employee.query.all()
    return jsonify([_serialize(e) for e in employees]), 200


@bp.route("/<int:employee_id>", methods=["GET"])
@manager_required
def get_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return jsonify(_serialize(employee)), 200


@bp.route("", methods=["POST"])
@manager_required
def create_employee():
    data = request.get_json(silent=True) or {}

    required = ["full_name", "email", "role_id"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not Role.query.get(data["role_id"]):
        return jsonify({"error": "Invalid role_id"}), 400

    email = str(data["email"]).strip().lower()
    if Employee.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    password = data.get("password")
    access_level = data.get("access_level", ACCESS_EMPLOYEE)
    if password:
        error = _validate_account_fields(password, access_level)
        if error:
            return jsonify({"error": error}), 400

    employee = Employee(
        full_name=data["full_name"],
        email=email,
        phone=data.get("phone"),
        role_id=data["role_id"],
    )
    db.session.add(employee)

    if password:
        account = UserAccount(employee=employee, access_level=access_level)
        account.set_password(password)
        db.session.add(account)

    db.session.commit()

    return jsonify(_serialize(employee)), 201


@bp.route("/<int:employee_id>", methods=["PUT"])
@manager_required
def update_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json(silent=True) or {}
    is_self = employee.id == g.current_account.employee_id

    if "email" in data:
        email = str(data["email"]).strip().lower()
        if email != employee.email:
            if Employee.query.filter_by(email=email).first():
                return jsonify({"error": "Email already in use"}), 409
            employee.email = email

    if "role_id" in data:
        if not Role.query.get(data["role_id"]):
            return jsonify({"error": "Invalid role_id"}), 400
        employee.role_id = data["role_id"]

    if is_self and data.get("is_active") is False:
        return jsonify({"error": "You cannot deactivate your own account"}), 400

    error = _apply_account_changes(employee, data)
    if error:
        return jsonify({"error": error}), 400

    employee.full_name = data.get("full_name", employee.full_name)
    employee.phone = data.get("phone", employee.phone)
    employee.is_active = data.get("is_active", employee.is_active)

    db.session.commit()
    return jsonify(_serialize(employee)), 200


@bp.route("/<int:employee_id>", methods=["DELETE"])
@manager_required
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)

    if employee.id == g.current_account.employee_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    db.session.delete(employee)
    db.session.commit()
    return "", 204


def _validate_account_fields(password, access_level):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if access_level not in VALID_ACCESS_LEVELS:
        return "access_level must be 'manager' or 'employee'"
    return None


def _apply_account_changes(employee, data):
    """Create an account, reset a password, or change the access level. Returns an error message or None."""
    password = data.get("password")
    access_level = data.get("access_level")

    if not password and access_level is None:
        return None

    if access_level is not None and access_level not in VALID_ACCESS_LEVELS:
        return "access_level must be 'manager' or 'employee'"
    if password and (not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH):
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"

    account = employee.account
    if account is None:
        if not password:
            return "A password is required to create an account"
        account = UserAccount(employee=employee, access_level=access_level or ACCESS_EMPLOYEE)
        db.session.add(account)
    elif access_level is not None:
        if employee.id == g.current_account.employee_id and access_level != ACCESS_MANAGER:
            return "You cannot remove your own manager access"
        account.access_level = access_level

    if password:
        account.set_password(password)
    return None


def _serialize(employee):
    return {
        "id": employee.id,
        "full_name": employee.full_name,
        "email": employee.email,
        "phone": employee.phone,
        "role": employee.role.name,
        "hire_date": employee.hire_date.isoformat(),
        "is_active": employee.is_active,
        "has_account": employee.account is not None,
        "access_level": employee.account.access_level if employee.account else None,
    }
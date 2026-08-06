from flask import Blueprint, request, jsonify
from app import db
from app.models import Employee, Role

bp = Blueprint("employees", __name__, url_prefix="/api/employees")


@bp.route("", methods=["GET"])
def list_employees():
    employees = Employee.query.all()
    return jsonify([convert_to_dict(e) for e in employees]), 200


@bp.route("/<int:employee_id>", methods=["GET"])
def get_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    return jsonify(convert_to_dict(employee)), 200


@bp.route("", methods=["POST"])
def create_employee():
    data = request.get_json()

    required = ["full_name", "email", "role_id"]
    missing = [r for r in required if r not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not Role.query.get(data["role_id"]):
        return jsonify({"error": "Invalid role_id"}), 400

    if Employee.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already in use"}), 409

    employee = Employee(
        full_name=data["full_name"],
        email=data["email"],
        phone=data.get("phone"),
        role_id=data["role_id"],
    )
    db.session.add(employee)
    db.session.commit()

    return jsonify(convert_to_dict(employee)), 201


@bp.route("/<int:employee_id>", methods=["PUT"])
def update_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    data = request.get_json()

    if "email" in data and data["email"] != employee.email:
        if Employee.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already in use"}), 409
        employee.email = data["email"]

    if "role_id" in data:
        if not Role.query.get(data["role_id"]):
            return jsonify({"error": "Invalid role_id"}), 400
        employee.role_id = data["role_id"]

    employee.full_name = data.get("full_name", employee.full_name)
    employee.phone = data.get("phone", employee.phone)
    employee.is_active = data.get("is_active", employee.is_active)

    db.session.commit()
    return jsonify(convert_to_dict(employee)), 200


@bp.route("/<int:employee_id>", methods=["DELETE"])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return "", 204


def convert_to_dict(employee):
    return {
        "id": employee.id,
        "full_name": employee.full_name,
        "email": employee.email,
        "phone": employee.phone,
        "role": employee.role.name,
        "hire_date": employee.hire_date.isoformat(),
        "is_active": employee.is_active,
    }
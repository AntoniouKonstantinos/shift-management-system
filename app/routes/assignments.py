from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import ShiftAssignment, Shift, Employee
from app.scheduler import get_available_employees, _is_available, _has_conflict, _is_on_time_off
from app.security import login_required, manager_required

bp = Blueprint("assignments", __name__, url_prefix="/api")

VALID_STATUSES = {"assigned", "confirmed", "completed", "no_show"}


@bp.route("/shifts/<int:shift_id>/candidates", methods=["GET"])
@manager_required
def list_candidates(shift_id):
    Shift.query.get_or_404(shift_id)
    candidates = get_available_employees(shift_id)
    return jsonify([
        {"id": e.id, "full_name": e.full_name, "role": e.role.name}
        for e in candidates
    ]), 200


@bp.route("/shifts/<int:shift_id>/assign", methods=["POST"])
@manager_required
def assign_employee(shift_id):
    shift = Shift.query.get_or_404(shift_id)
    data = request.get_json()

    if "employee_id" not in data:
        return jsonify({"error": "Missing field: employee_id"}), 400

    employee = Employee.query.get(data["employee_id"])
    if not employee:
        return jsonify({"error": "Invalid employee_id"}), 400

    if not employee.is_active:
        return jsonify({"error": "Employee is not active"}), 400

    existing = ShiftAssignment.query.filter_by(
        employee_id=employee.id, shift_id=shift.id
    ).first()
    if existing:
        return jsonify({"error": "Employee is already assigned to this shift"}), 409

    day_of_week = shift.shift_date.weekday()
    force = data.get("force", False)

    if not force:
        if not _is_available(employee, day_of_week, shift.start_time, shift.end_time):
            return jsonify({"error": "Employee has not declared availability for this time"}), 409
        if _has_conflict(employee, shift):
            return jsonify({"error": "Employee has a conflicting shift assignment"}), 409
        if _is_on_time_off(employee, shift.shift_date):
            return jsonify({"error": "Employee is on approved time off"}), 409

    assignment = ShiftAssignment(
        employee_id=employee.id,
        shift_id=shift.id,
        status="assigned",
    )
    db.session.add(assignment)
    db.session.commit()

    return jsonify(_serialize(assignment)), 201


@bp.route("/assignments/<int:assignment_id>", methods=["PATCH"])
@manager_required
def update_assignment_status(assignment_id):
    assignment = ShiftAssignment.query.get_or_404(assignment_id)
    data = request.get_json()

    new_status = data.get("status")
    if new_status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    assignment.status = new_status

    if new_status == "completed":
        assignment.check_out = datetime.utcnow()

    db.session.commit()
    return jsonify(_serialize(assignment)), 200


@bp.route("/assignments/<int:assignment_id>/check-in", methods=["PATCH"])
@login_required
def check_in(assignment_id):
    assignment = ShiftAssignment.query.get_or_404(assignment_id)
    account = g.current_account

    if not account.is_manager and assignment.employee_id != account.employee_id:
        return jsonify({"error": "You can only check in to your own shifts"}), 403

    assignment.check_in = datetime.utcnow()
    db.session.commit()
    return jsonify(_serialize(assignment)), 200


@bp.route("/assignments/<int:assignment_id>", methods=["DELETE"])
@manager_required
def remove_assignment(assignment_id):
    assignment = ShiftAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    return "", 204


def _serialize(assignment):
    return {
        "id": assignment.id,
        "employee_id": assignment.employee_id,
        "employee_name": assignment.employee.full_name,
        "shift_id": assignment.shift_id,
        "status": assignment.status,
        "check_in": assignment.check_in.isoformat() if assignment.check_in else None,
        "check_out": assignment.check_out.isoformat() if assignment.check_out else None,
    }
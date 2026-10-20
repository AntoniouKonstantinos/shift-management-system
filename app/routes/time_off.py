from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import TimeOffRequest, Employee
from app.security import login_required, manager_required

bp = Blueprint("time_off", __name__, url_prefix="/api/time-off")


@bp.route("", methods=["GET"])
@login_required
def list_time_off():
    account = g.current_account
    query = TimeOffRequest.query

    if account.is_manager:
        employee_id = request.args.get("employee_id", type=int)
        if employee_id:
            query = query.filter_by(employee_id=employee_id)
    else:
        query = query.filter_by(employee_id=account.employee_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    requests = query.order_by(TimeOffRequest.start_date).all()
    return jsonify([_serialize(r) for r in requests]), 200


@bp.route("/<int:request_id>", methods=["GET"])
@login_required
def get_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)
    if not _can_access(req):
        return jsonify({"error": "You can only view your own requests"}), 403
    return jsonify(_serialize(req)), 200


@bp.route("", methods=["POST"])
@login_required
def create_time_off():
    account = g.current_account
    data = request.get_json(silent=True) or {}

    required = ["start_date", "end_date"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if account.is_manager:
        employee_id = data.get("employee_id", account.employee_id)
        if not Employee.query.get(employee_id):
            return jsonify({"error": "Invalid employee_id"}), 400
    else:
        employee_id = account.employee_id

    start_date = _parse_date(data["start_date"])
    end_date = _parse_date(data["end_date"])

    if start_date > end_date:
        return jsonify({"error": "start_date must be before or equal to end_date"}), 400

    req = TimeOffRequest(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=data.get("reason"),
        status="pending",
    )
    db.session.add(req)
    db.session.commit()

    return jsonify(_serialize(req)), 201


@bp.route("/<int:request_id>/approve", methods=["PATCH"])
@manager_required
def approve_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)

    if req.status != "pending":
        return jsonify({"error": f"Request is already {req.status}"}), 409

    req.status = "approved"
    db.session.commit()
    return jsonify(_serialize(req)), 200


@bp.route("/<int:request_id>/reject", methods=["PATCH"])
@manager_required
def reject_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)

    if req.status != "pending":
        return jsonify({"error": f"Request is already {req.status}"}), 409

    req.status = "rejected"
    db.session.commit()
    return jsonify(_serialize(req)), 200


@bp.route("/<int:request_id>", methods=["DELETE"])
@login_required
def delete_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)
    account = g.current_account

    if not account.is_manager:
        if req.employee_id != account.employee_id:
            return jsonify({"error": "You can only delete your own requests"}), 403
        if req.status != "pending":
            return jsonify({"error": "Only pending requests can be withdrawn"}), 409

    db.session.delete(req)
    db.session.commit()
    return "", 204


def _can_access(req):
    account = g.current_account
    return account.is_manager or req.employee_id == account.employee_id


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _serialize(req):
    return {
        "id": req.id,
        "employee_id": req.employee_id,
        "employee_name": req.employee.full_name,
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "reason": req.reason,
        "status": req.status,
    }
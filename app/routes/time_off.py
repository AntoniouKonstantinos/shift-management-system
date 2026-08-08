from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import TimeOffRequest, Employee

bp = Blueprint("time_off", __name__, url_prefix="/api/time-off")


@bp.route("", methods=["GET"])
def list_time_off():
    query = TimeOffRequest.query

    employee_id = request.args.get("employee_id", type=int)
    if employee_id:
        query = query.filter_by(employee_id=employee_id)

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    requests = query.order_by(TimeOffRequest.start_date).all()
    return jsonify([convert_to_dict(r) for r in requests]), 200


@bp.route("/<int:request_id>", methods=["GET"])
def get_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)
    return jsonify(convert_to_dict(req)), 200


@bp.route("", methods=["POST"])
def create_time_off():
    data = request.get_json()

    required = ["employee_id", "start_date", "end_date"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not Employee.query.get(data["employee_id"]):
        return jsonify({"error": "Invalid employee_id"}), 400

    start_date = _parse_date(data["start_date"])
    end_date = _parse_date(data["end_date"])

    if start_date > end_date:
        return jsonify({"error": "start_date must be before or equal to end_date"}), 400

    req = TimeOffRequest(
        employee_id=data["employee_id"],
        start_date=start_date,
        end_date=end_date,
        reason=data.get("reason"),
        status="pending",
    )
    db.session.add(req)
    db.session.commit()

    return jsonify(convert_to_dict(req)), 201


@bp.route("/<int:request_id>/approve", methods=["PATCH"])
def approve_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)

    if req.status != "pending":
        return jsonify({"error": f"Request is already {req.status}"}), 409

    req.status = "approved"
    db.session.commit()
    return jsonify(convert_to_dict(req)), 200


@bp.route("/<int:request_id>/reject", methods=["PATCH"])
def reject_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)

    if req.status != "pending":
        return jsonify({"error": f"Request is already {req.status}"}), 409

    req.status = "rejected"
    db.session.commit()
    return jsonify(convert_to_dict(req)), 200


@bp.route("/<int:request_id>", methods=["DELETE"])
def delete_time_off(request_id):
    req = TimeOffRequest.query.get_or_404(request_id)
    db.session.delete(req)
    db.session.commit()
    return "", 204


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def convert_to_dict(req):
    return {
        "id": req.id,
        "employee_id": req.employee_id,
        "employee_name": req.employee.full_name,
        "start_date": req.start_date.isoformat(),
        "end_date": req.end_date.isoformat(),
        "reason": req.reason,
        "status": req.status,
    }
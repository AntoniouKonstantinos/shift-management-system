from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import Shift, Department

bp = Blueprint("shifts", __name__, url_prefix="/api/shifts")


@bp.route("", methods=["GET"])
def list_shifts():
    query = Shift.query

    department_id = request.args.get("department_id", type=int)
    if department_id:
        query = query.filter_by(department_id=department_id)

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    if date_from:
        query = query.filter(Shift.shift_date >= _parse_date(date_from))
    if date_to:
        query = query.filter(Shift.shift_date <= _parse_date(date_to))

    shifts = query.order_by(Shift.shift_date, Shift.start_time).all()
    return jsonify([convert_to_dict(sh) for sh in shifts]), 200


@bp.route("/<int:shift_id>", methods=["GET"])
def get_shift(shift_id):
    shift = Shift.query.get_or_404(shift_id)
    return jsonify(convert_to_dict(shift, include_assignments=True)), 200


@bp.route("", methods=["POST"])
def create_shift():
    data = request.get_json()

    required = ["department_id", "shift_date", "start_time", "end_time"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not Department.query.get(data["department_id"]):
        return jsonify({"error": "Invalid department_id"}), 400

    shift_date = _parse_date(data["shift_date"])
    start_time = _parse_time(data["start_time"])
    end_time = _parse_time(data["end_time"])

    if start_time >= end_time:
        return jsonify({"error": "Start time must be before end time"}), 400

    shift = Shift(
        department_id=data["department_id"],
        shift_date=shift_date,
        start_time=start_time,
        end_time=end_time,
        required_staff=data.get("required_staff", 1),
        notes=data.get("notes"),
    )
    db.session.add(shift)
    db.session.commit()

    return jsonify(convert_to_dict(shift)), 201


@bp.route("/<int:shift_id>", methods=["PUT"])
def update_shift(shift_id):
    shift = Shift.query.get_or_404(shift_id)
    data = request.get_json()

    if "department_id" in data:
        if not Department.query.get(data["department_id"]):
            return jsonify({"error": "Invalid department_id"}), 400
        shift.department_id = data["department_id"]

    if "shift_date" in data:
        shift.shift_date = _parse_date(data["shift_date"])
    if "start_time" in data:
        shift.start_time = _parse_time(data["start_time"])
    if "end_time" in data:
        shift.end_time = _parse_time(data["end_time"])

    if shift.start_time >= shift.end_time:
        return jsonify({"error": "start_time must be before end_time"}), 400

    shift.required_staff = data.get("required_staff", shift.required_staff)
    shift.notes = data.get("notes", shift.notes)

    db.session.commit()
    return jsonify(convert_to_dict(shift)), 200


@bp.route("/<int:shift_id>", methods=["DELETE"])
def delete_shift(shift_id):
    shift = Shift.query.get_or_404(shift_id)
    db.session.delete(shift)
    db.session.commit()
    return "", 204


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def convert_to_dict(shift, include_assignments=False):
    data = {
        "id": shift.id,
        "department": shift.department.name,
        "shift_date": shift.shift_date.isoformat(),
        "start_time": shift.start_time.strftime("%H:%M"),
        "end_time": shift.end_time.strftime("%H:%M"),
        "required_staff": shift.required_staff,
        "assigned_count": len(shift.assignments),
        "notes": shift.notes,
    }
    if include_assignments:
        data["assignments"] = [
            {
                "id": s_a.id,
                "employee": s_a.employee.full_name,
                "status": s_a.status,
            }
            for s_a in shift.assignments
        ]
    return data
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from app import db
from app.models import Availability, Employee
from app.security import login_required

bp = Blueprint("availability", __name__, url_prefix="/api/employees/<int:employee_id>/availability")


@bp.route("", methods=["GET"])
@login_required
def list_availability(employee_id):
    forbidden = _forbidden_unless_self_or_manager(employee_id)
    if forbidden:
        return forbidden

    Employee.query.get_or_404(employee_id)
    slots = Availability.query.filter_by(employee_id=employee_id).order_by(
        Availability.day_of_week, Availability.start_time
    ).all()
    return jsonify([_serialize(s) for s in slots]), 200


@bp.route("", methods=["POST"])
@login_required
def create_availability(employee_id):
    forbidden = _forbidden_unless_self_or_manager(employee_id)
    if forbidden:
        return forbidden

    Employee.query.get_or_404(employee_id)
    data = request.get_json()

    required = ["day_of_week", "start_time", "end_time"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    day_of_week = data["day_of_week"]
    if not isinstance(day_of_week, int) or not (0 <= day_of_week <= 6):
        return jsonify({"error": "day_of_week must be an integer 0-6"}), 400

    start_time = _parse_time(data["start_time"])
    end_time = _parse_time(data["end_time"])

    if start_time >= end_time:
        return jsonify({"error": "start_time must be before end_time"}), 400

    if _overlaps_existing(employee_id, day_of_week, start_time, end_time):
        return jsonify({"error": "Overlaps with an existing availability slot"}), 409

    slot = Availability(
        employee_id=employee_id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
    )
    db.session.add(slot)
    db.session.commit()

    return jsonify(_serialize(slot)), 201


@bp.route("/<int:slot_id>", methods=["PUT"])
@login_required
def update_availability(employee_id, slot_id):
    forbidden = _forbidden_unless_self_or_manager(employee_id)
    if forbidden:
        return forbidden

    slot = Availability.query.filter_by(id=slot_id, employee_id=employee_id).first_or_404()
    data = request.get_json()

    day_of_week = data.get("day_of_week", slot.day_of_week)
    if not isinstance(day_of_week, int) or not (0 <= day_of_week <= 6):
        return jsonify({"error": "day_of_week must be an integer 0-6"}), 400

    start_time = _parse_time(data["start_time"]) if "start_time" in data else slot.start_time
    end_time = _parse_time(data["end_time"]) if "end_time" in data else slot.end_time

    if start_time >= end_time:
        return jsonify({"error": "start_time must be before end_time"}), 400

    if _overlaps_existing(employee_id, day_of_week, start_time, end_time, exclude_id=slot.id):
        return jsonify({"error": "Overlaps with an existing availability slot"}), 409

    slot.day_of_week = day_of_week
    slot.start_time = start_time
    slot.end_time = end_time

    db.session.commit()
    return jsonify(_serialize(slot)), 200


@bp.route("/<int:slot_id>", methods=["DELETE"])
@login_required
def delete_availability(employee_id, slot_id):
    forbidden = _forbidden_unless_self_or_manager(employee_id)
    if forbidden:
        return forbidden

    slot = Availability.query.filter_by(id=slot_id, employee_id=employee_id).first_or_404()
    db.session.delete(slot)
    db.session.commit()
    return "", 204


def _forbidden_unless_self_or_manager(employee_id):
    """Return a 403 response when a non-manager touches someone else's data, otherwise None."""
    account = g.current_account
    if account.is_manager or account.employee_id == employee_id:
        return None
    return jsonify({"error": "You can only manage your own availability"}), 403


def _overlaps_existing(employee_id, day_of_week, start_time, end_time, exclude_id=None):
    query = Availability.query.filter_by(employee_id=employee_id, day_of_week=day_of_week)
    if exclude_id:
        query = query.filter(Availability.id != exclude_id)

    for slot in query.all():
        if start_time < slot.end_time and slot.start_time < end_time:
            return True
    return False


def _parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def _serialize(slot):
    return {
        "id": slot.id,
        "employee_id": slot.employee_id,
        "day_of_week": slot.day_of_week,
        "start_time": slot.start_time.strftime("%H:%M"),
        "end_time": slot.end_time.strftime("%H:%M"),
    }
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload, selectinload
from app import db
from app.models import Shift, ShiftAssignment, Department
from app.security import login_required, manager_required
from app.timeutils import crosses_midnight, is_valid_range

bp = Blueprint("shifts", __name__, url_prefix="/api/shifts")

REQUIRED_STAFF_ERROR = "required_staff must be a whole number of at least 1"
NOTES_ERROR = "notes must be text of at most 255 characters"
MAX_NOTES_LENGTH = 255


@bp.route("", methods=["GET"])
@login_required
def list_shifts():
    query = Shift.query.options(
        joinedload(Shift.department),
        selectinload(Shift.assignments).joinedload(ShiftAssignment.employee),
    )

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
    return jsonify([_serialize(s) for s in shifts]), 200


@bp.route("/<int:shift_id>", methods=["GET"])
@login_required
def get_shift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    return jsonify(_serialize(shift)), 200


@bp.route("", methods=["POST"])
@manager_required
def create_shift():
    data = request.get_json()

    required = ["department_id", "shift_date", "start_time", "end_time"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not db.session.get(Department, data["department_id"]):
        return jsonify({"error": "Invalid department_id"}), 400

    shift_date = _parse_date(data["shift_date"])
    start_time = _parse_time(data["start_time"])
    end_time = _parse_time(data["end_time"])

    if not is_valid_range(start_time, end_time):
        return jsonify({"error": "start_time and end_time cannot be the same"}), 400

    required_staff = data.get("required_staff", 1)
    if _invalid_required_staff(required_staff):
        return jsonify({"error": REQUIRED_STAFF_ERROR}), 400

    notes = data.get("notes")
    if _invalid_notes(notes):
        return jsonify({"error": NOTES_ERROR}), 400

    shift = Shift(
        department_id=data["department_id"],
        shift_date=shift_date,
        start_time=start_time,
        end_time=end_time,
        required_staff=required_staff,
        notes=notes,
    )
    db.session.add(shift)
    db.session.commit()

    return jsonify(_serialize(shift)), 201


@bp.route("/duplicate-week", methods=["POST"])
@manager_required
def duplicate_week():
    """Copy every shift of one week onto another week. Assignments are not copied."""
    data = request.get_json(silent=True) or {}

    try:
        source_start = _parse_date(data.get("source_week_start"))
        target_start = _parse_date(data.get("target_week_start"))
    except (ValueError, TypeError):
        return jsonify({
            "error": "source_week_start and target_week_start must be dates in the format YYYY-MM-DD"
        }), 400

    if source_start.weekday() != 0 or target_start.weekday() != 0:
        return jsonify({"error": "Both dates must be the Monday that starts a week"}), 400
    if source_start == target_start:
        return jsonify({"error": "The target week must be different from the source week"}), 400

    source_end = source_start + timedelta(days=6)
    target_end = target_start + timedelta(days=6)
    offset = target_start - source_start

    source_shifts = Shift.query.filter(
        Shift.shift_date >= source_start, Shift.shift_date <= source_end
    ).all()

    already_there = {
        (s.department_id, s.shift_date, s.start_time, s.end_time)
        for s in Shift.query.filter(
            Shift.shift_date >= target_start, Shift.shift_date <= target_end
        )
    }

    created = 0
    skipped = 0
    for shift in source_shifts:
        new_date = shift.shift_date + offset
        if (shift.department_id, new_date, shift.start_time, shift.end_time) in already_there:
            skipped += 1
            continue

        db.session.add(Shift(
            department_id=shift.department_id,
            shift_date=new_date,
            start_time=shift.start_time,
            end_time=shift.end_time,
            required_staff=shift.required_staff,
            notes=shift.notes,
        ))
        created += 1

    db.session.commit()
    return jsonify({"created": created, "skipped": skipped}), (201 if created else 200)


@bp.route("/<int:shift_id>", methods=["PUT"])
@manager_required
def update_shift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    data = request.get_json()

    if "required_staff" in data and _invalid_required_staff(data["required_staff"]):
        return jsonify({"error": REQUIRED_STAFF_ERROR}), 400
    if "notes" in data and _invalid_notes(data["notes"]):
        return jsonify({"error": NOTES_ERROR}), 400

    if "department_id" in data:
        if not db.session.get(Department, data["department_id"]):
            return jsonify({"error": "Invalid department_id"}), 400
        shift.department_id = data["department_id"]

    if "shift_date" in data:
        shift.shift_date = _parse_date(data["shift_date"])
    if "start_time" in data:
        shift.start_time = _parse_time(data["start_time"])
    if "end_time" in data:
        shift.end_time = _parse_time(data["end_time"])

    if not is_valid_range(shift.start_time, shift.end_time):
        return jsonify({"error": "start_time and end_time cannot be the same"}), 400

    shift.required_staff = data.get("required_staff", shift.required_staff)
    shift.notes = data.get("notes", shift.notes)

    db.session.commit()
    return jsonify(_serialize(shift)), 200


@bp.route("/<int:shift_id>", methods=["DELETE"])
@manager_required
def delete_shift(shift_id):
    shift = db.get_or_404(Shift, shift_id)
    db.session.delete(shift)
    db.session.commit()
    return "", 204


def _invalid_required_staff(value):
    # bool is a subclass of int in Python, so True/False must be rejected explicitly
    return not isinstance(value, int) or isinstance(value, bool) or value < 1


def _invalid_notes(value):
    return value is not None and (not isinstance(value, str) or len(value) > MAX_NOTES_LENGTH)


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def _serialize(shift):
    return {
        "id": shift.id,
        "department_id": shift.department_id,
        "department": shift.department.name,
        "shift_date": shift.shift_date.isoformat(),
        "start_time": shift.start_time.strftime("%H:%M"),
        "end_time": shift.end_time.strftime("%H:%M"),
        "ends_next_day": crosses_midnight(shift.start_time, shift.end_time),
        "required_staff": shift.required_staff,
        "assigned_count": len(shift.assignments),
        "notes": shift.notes,
        "assignments": [
            {
                "id": a.id,
                "employee_id": a.employee_id,
                "employee": a.employee.full_name,
                "status": a.status,
            }
            for a in shift.assignments
        ],
    }
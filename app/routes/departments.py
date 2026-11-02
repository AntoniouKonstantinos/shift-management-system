from flask import Blueprint, jsonify
from app.models import Department
from app.security import login_required

bp = Blueprint("departments", __name__, url_prefix="/api/departments")


@bp.route("", methods=["GET"])
@login_required
def list_departments():
    departments = Department.query.order_by(Department.name).all()
    return jsonify([_serialize(d) for d in departments]), 200


def _serialize(department):
    return {
        "id": department.id,
        "name": department.name,
    }
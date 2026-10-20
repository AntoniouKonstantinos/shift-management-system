from flask import Blueprint, jsonify
from app.models import Role
from app.security import login_required

bp = Blueprint("roles", __name__, url_prefix="/api/roles")


@bp.route("", methods=["GET"])
@login_required
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify([_serialize(r) for r in roles]), 200


def _serialize(role):
    return {
        "id": role.id,
        "name": role.name,
        "hourly_rate": role.hourly_rate,
    }
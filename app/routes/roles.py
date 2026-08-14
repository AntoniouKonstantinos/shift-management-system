from flask import Blueprint, jsonify
from app.models import Role

bp = Blueprint("roles", __name__, url_prefix="/api/roles")


@bp.route("", methods=["GET"])
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify([_to_dictionary(r) for r in roles]), 200


def _to_dictionary(role):
    return {
        "id": role.id,
        "name": role.name,
        "hourly_rate": role.hourly_rate,
    }
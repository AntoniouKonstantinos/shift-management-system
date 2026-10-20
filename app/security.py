from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app import db
from app.models import UserAccount


def register_jwt_callbacks(jwt):
    """Make every authentication failure use the same {"error": ...} shape as the rest of the API."""

    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authentication required"}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token"}), 401

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401


def _authenticate():
    """Validate the token and return the matching, still-valid account (or None)."""
    verify_jwt_in_request()

    account_id = get_jwt_identity()
    if account_id is None:
        return None

    account = db.session.get(UserAccount, int(account_id))
    if account is None or not account.employee.is_active:
        return None
    return account


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        account = _authenticate()
        if account is None:
            return jsonify({"error": "Account is not valid"}), 401
        g.current_account = account
        return fn(*args, **kwargs)

    return wrapper


def manager_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        account = _authenticate()
        if account is None:
            return jsonify({"error": "Account is not valid"}), 401
        if not account.is_manager:
            return jsonify({"error": "Manager access required"}), 403
        g.current_account = account
        return fn(*args, **kwargs)

    return wrapper
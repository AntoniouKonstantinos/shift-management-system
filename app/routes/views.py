from flask import Blueprint, render_template

bp = Blueprint("views", __name__)


@bp.route("/")
def dashboard():
    return render_template("dashboard.html")


@bp.route("/employees")
def employees_page():
    return render_template("employees.html")


@bp.route("/time-off")
def time_off_page():
    return render_template("time_off.html")
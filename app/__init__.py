from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)

    from app.security import register_jwt_callbacks
    register_jwt_callbacks(jwt)

    from app.routes.auth import bp as auth_bp
    from app.routes.employees import bp as employees_bp
    from app.routes.shifts import bp as shifts_bp
    from app.routes.assignments import bp as assignments_bp
    from app.routes.availability import bp as availability_bp
    from app.routes.time_off import bp as time_off_bp
    from app.routes.roles import bp as roles_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(shifts_bp)
    app.register_blueprint(assignments_bp)
    app.register_blueprint(availability_bp)
    app.register_blueprint(time_off_bp)
    app.register_blueprint(roles_bp)

    with app.app_context():
        from app import models
        db.create_all()

    return app
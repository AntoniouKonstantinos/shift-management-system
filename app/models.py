from datetime import datetime
from app import db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # "Waiter", "Chef", "Bartender" etc.
    hourly_rate = db.Column(db.Float, nullable=True)

    employees = db.relationship("Employee", back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # "Kitchen", "Bar", "Floor" etc.

    shifts = db.relationship("Shift", back_populates="department")

    def __repr__(self):
        return f"<Department {self.name}>"


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    hire_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    role = db.relationship("Role", back_populates="employees")
    availabilities = db.relationship("Availability", back_populates="employee", cascade="all, delete-orphan")
    time_off_requests = db.relationship("TimeOffRequest", back_populates="employee", cascade="all, delete-orphan")
    shift_assignments = db.relationship("ShiftAssignment", back_populates="employee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.full_name}>"


class Shift(db.Model):
    __tablename__ = "shifts"

    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    required_staff = db.Column(db.Integer, default=1)
    notes = db.Column(db.String(255), nullable=True)

    department = db.relationship("Department", back_populates="shifts")
    assignments = db.relationship("ShiftAssignment", back_populates="shift", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Shift {self.shift_date} {self.start_time}-{self.end_time}>"


class ShiftAssignment(db.Model):
    """Junction table Employee <-> Shift."""
    __tablename__ = "shift_assignments"
    __table_args__ = (
        db.UniqueConstraint("employee_id", "shift_id", name="uq_employee_shift"),
    )

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"), nullable=False)
    status = db.Column(db.String(20), default="assigned")  # assigned / confirmed / completed / no_show
    check_in = db.Column(db.DateTime, nullable=True)
    check_out = db.Column(db.DateTime, nullable=True)

    employee = db.relationship("Employee", back_populates="shift_assignments")
    shift = db.relationship("Shift", back_populates="assignments")

    def __repr__(self):
        return f"<Assignment emp={self.employee_id} shift={self.shift_id} status={self.status}>"


class Availability(db.Model):
    """Availability per day of the week (0=Monday... 6=Sunday)."""
    __tablename__ = "availabilities"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    employee = db.relationship("Employee", back_populates="availabilities")


class TimeOffRequest(db.Model):
    __tablename__ = "time_off_requests"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending / approved / rejected

    employee = db.relationship("Employee", back_populates="time_off_requests")
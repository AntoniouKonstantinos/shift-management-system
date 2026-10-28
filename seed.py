from datetime import date, time, timedelta
from app import create_app, db
from app.models import (
    Role, Department, Employee, UserAccount, Shift, Availability,
    ACCESS_MANAGER, ACCESS_EMPLOYEE,
)

MANAGER_PASSWORD = "manager123"
EMPLOYEE_PASSWORD = "employee123"

app = create_app()


def add_account(employee, password, access_level):
    account = UserAccount(employee=employee, access_level=access_level)
    account.set_password(password)
    db.session.add(account)


with app.app_context():
    db.drop_all()
    db.create_all()

    # Roles
    waiter = Role(name="Waiter", hourly_rate=6.5)
    chef = Role(name="Chef", hourly_rate=9.0)
    bartender = Role(name="Bartender", hourly_rate=7.5)
    host = Role(name="Host", hourly_rate=6.0)
    manager_role = Role(name="Manager", hourly_rate=11.0)
    db.session.add_all([waiter, chef, bartender, host, manager_role])
    db.session.commit()

    # Departments
    kitchen = Department(name="Kitchen")
    bar = Department(name="Bar")
    floor = Department(name="Floor")
    db.session.add_all([kitchen, bar, floor])
    db.session.commit()

    # Employees
    anna = Employee(full_name="Anna Vasileiou", email="manager@example.com",
                    role_id=manager_role.id, hire_date=date(2021, 9, 1))
    maria = Employee(full_name="Maria Papadopoulou", email="maria@example.com",
                     role_id=waiter.id, hire_date=date(2023, 3, 1))
    nikos = Employee(full_name="Nikos Georgiou", email="nikos@example.com",
                     role_id=chef.id, hire_date=date(2022, 6, 15))
    elena = Employee(full_name="Elena Ioannou", email="elena@example.com",
                     role_id=bartender.id, hire_date=date(2024, 1, 10))
    db.session.add_all([anna, maria, nikos, elena])
    db.session.commit()

    # Accounts
    add_account(anna, MANAGER_PASSWORD, ACCESS_MANAGER)
    add_account(maria, EMPLOYEE_PASSWORD, ACCESS_EMPLOYEE)
    add_account(nikos, EMPLOYEE_PASSWORD, ACCESS_EMPLOYEE)
    add_account(elena, EMPLOYEE_PASSWORD, ACCESS_EMPLOYEE)
    db.session.commit()

    # Availability — Maria: Mon-Fri evenings
    for day in range(0, 5):
        db.session.add(Availability(
            employee_id=maria.id, day_of_week=day,
            start_time=time(17, 0), end_time=time(23, 0)
        ))

    # Availability — Nikos: every day, all day
    for day in range(0, 7):
        db.session.add(Availability(
            employee_id=nikos.id, day_of_week=day,
            start_time=time(10, 0), end_time=time(23, 0)
        ))

    # Availability — Elena: Friday and Saturday until 02:00 (overnight), Sunday evening
    for day in (4, 5):
        db.session.add(Availability(
            employee_id=elena.id, day_of_week=day,
            start_time=time(17, 0), end_time=time(2, 0)
        ))
    db.session.add(Availability(
        employee_id=elena.id, day_of_week=6,
        start_time=time(16, 0), end_time=time(23, 0)
    ))

    db.session.commit()

    # Shifts — next 7 days
    today = date.today()
    for i in range(7):
        shift_date = today + timedelta(days=i)
        db.session.add(Shift(
            department_id=floor.id, shift_date=shift_date,
            start_time=time(17, 0), end_time=time(23, 0), required_staff=2
        ))
        db.session.add(Shift(
            department_id=kitchen.id, shift_date=shift_date,
            start_time=time(11, 0), end_time=time(22, 0), required_staff=1
        ))
        db.session.add(Shift(
            department_id=bar.id, shift_date=shift_date,
            start_time=time(20, 0), end_time=time(2, 0), required_staff=1
        ))

    db.session.commit()

    print("Seed complete: 5 roles, 3 departments, 4 employees, 4 accounts, availability, 21 shifts.")
    print()
    print("Demo logins (local development only):")
    print(f"  manager   manager@example.com   / {MANAGER_PASSWORD}")
    print(f"  employee  maria@example.com     / {EMPLOYEE_PASSWORD}")
    print(f"  employee  nikos@example.com     / {EMPLOYEE_PASSWORD}")
    print(f"  employee  elena@example.com     / {EMPLOYEE_PASSWORD}")
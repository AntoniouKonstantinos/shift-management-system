from datetime import date

import pytest

from app import db
from app.models import ACCESS_EMPLOYEE, Employee, Role, UserAccount

EMAIL = "elena@example.com"
PASSWORD = "password123"
NEW_PASSWORD = "brandnewpass456"


def create_user():
    role = Role(name="Bartender", hourly_rate=7.5)
    db.session.add(role)
    db.session.commit()

    employee = Employee(
        full_name="Elena Ioannou", email=EMAIL, role_id=role.id, hire_date=date(2024, 1, 10)
    )
    db.session.add(employee)
    db.session.commit()

    account = UserAccount(employee=employee, access_level=ACCESS_EMPLOYEE)
    account.set_password(PASSWORD)
    db.session.add(account)
    db.session.commit()
    return employee


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    return create_user()


@pytest.fixture
def limited_client(limited_app):
    return limited_app.test_client()


@pytest.fixture
def limited_user(limited_app):
    return create_user()


def login(client, email=EMAIL, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def token_header(client, password=PASSWORD):
    token = login(client, password=password).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def change_password(client, headers, current, new):
    return client.post(
        "/api/auth/change-password",
        json={"current_password": current, "new_password": new},
        headers=headers,
    )


# --- login ---

def test_login_with_valid_credentials_returns_a_token(client, user):
    response = login(client)
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_with_a_wrong_password_is_rejected(client, user):
    response = login(client, password="not-the-password")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid email or password"


def test_login_ignores_email_case_and_surrounding_spaces(client, user):
    assert login(client, email="  ELENA@Example.com ").status_code == 200


# --- change password ---

def test_changing_the_password_replaces_the_old_one(client, user):
    headers = token_header(client)
    assert change_password(client, headers, PASSWORD, NEW_PASSWORD).status_code == 200
    assert login(client, password=PASSWORD).status_code == 401
    assert login(client, password=NEW_PASSWORD).status_code == 200


def test_wrong_current_password_is_forbidden_and_changes_nothing(client, user):
    headers = token_header(client)
    response = change_password(client, headers, "not-the-password", NEW_PASSWORD)
    assert response.status_code == 403
    assert login(client, password=PASSWORD).status_code == 200


def test_too_short_new_password_is_rejected(client, user):
    headers = token_header(client)
    assert change_password(client, headers, PASSWORD, "short").status_code == 400


def test_new_password_must_differ_from_the_current_one(client, user):
    headers = token_header(client)
    assert change_password(client, headers, PASSWORD, PASSWORD).status_code == 400


def test_both_fields_are_required(client, user):
    headers = token_header(client)
    response = client.post(
        "/api/auth/change-password", json={"new_password": NEW_PASSWORD}, headers=headers
    )
    assert response.status_code == 400


def test_changing_the_password_requires_authentication(client, user):
    response = client.post(
        "/api/auth/change-password",
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 401


# --- rate limiting ---

def test_login_is_blocked_after_five_failed_attempts(limited_client, limited_user):
    for _ in range(5):
        assert login(limited_client, password="wrong").status_code == 401

    response = login(limited_client, password="wrong")
    assert response.status_code == 429
    assert "error" in response.get_json()


def test_a_blocked_client_cannot_log_in_even_with_the_correct_password(limited_client, limited_user):
    for _ in range(5):
        login(limited_client, password="wrong")
    assert login(limited_client).status_code == 429


def test_successful_logins_do_not_use_up_the_limit(limited_client, limited_user):
    for _ in range(8):
        assert login(limited_client).status_code == 200


def test_wrong_current_password_attempts_are_limited(limited_client, limited_user):
    headers = token_header(limited_client)
    for _ in range(5):
        assert change_password(limited_client, headers, "wrong", NEW_PASSWORD).status_code == 403
    assert change_password(limited_client, headers, "wrong", NEW_PASSWORD).status_code == 429
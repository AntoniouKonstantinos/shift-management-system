import pytest

from app import create_app, db


@pytest.fixture
def app():
    """A fresh application with its own empty in-memory database for every test."""
    app = create_app("testing")
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()
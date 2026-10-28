import pytest

from app import create_app, db


def _app_with_database(config_name):
    """A fresh application with its own empty in-memory database."""
    app = create_app(config_name)
    with app.app_context():
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def app():
    """The normal test application (rate limiting switched off)."""
    yield from _app_with_database("testing")


@pytest.fixture
def limited_app():
    """A test application with rate limiting switched on."""
    yield from _app_with_database("testing_ratelimit")
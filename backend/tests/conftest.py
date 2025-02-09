# tests/conftest.py
import pytest
import fakeredis
from app import app  # Ensure this import points to your Flask app instance


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    # Create a fake Redis client that behaves like the real one
    fake_redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    # Override the redis_client in our app with the fake one
    monkeypatch.setattr("app.redis_client", fake_redis_client)
    yield fake_redis_client


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

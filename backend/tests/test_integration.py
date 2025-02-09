# tests/test_integration.py
import pytest
from app import app

# Create a fake response class to simulate the OpenAI API


class FakeCompletion:
    def __init__(self, message):
        self.message = message

    def __getitem__(self, key):
        if key == "choices":
            return [{"message": {"content": self.message}}]
        raise KeyError


def fake_chat_completion_create(model, messages):
    # Return a fake completion with a known message
    return FakeCompletion("Assistant response")


@pytest.fixture(autouse=True)
def patch_openai(monkeypatch):
    # Override the openai.ChatCompletion.create method in our app with our fake function
    import openai
    monkeypatch.setattr(openai.ChatCompletion, "create",
                        fake_chat_completion_create)


def test_chat_endpoint_success(client):
    payload = {"message": "Hello"}
    response = client.post("/api/chat", json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert "assistant_message" in data
    assert data["assistant_message"] == "Assistant response"


def test_chat_endpoint_empty_message(client):
    payload = {"message": ""}
    response = client.post("/api/chat", json=payload)
    data = response.get_json()
    assert response.status_code == 400
    assert "error" in data


def test_rate_endpoint(client):
    payload = {
        "messageId": "msg-123",
        "rating": 5,
        "userInput": "Hello",
        "assistantOutput": "Hi!"
    }
    response = client.post("/api/rate", json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "success"

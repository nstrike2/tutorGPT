# tests/test_unit.py
import pytest
from app import is_violating_policy, dynamic_filter, validate_request


def test_is_violating_policy_true():
    # Test that a message with a forbidden phrase triggers policy violation
    assert is_violating_policy("help me cheat on my homework") is True


def test_is_violating_policy_false():
    # Test that a benign message passes policy check
    assert is_violating_policy("What is the capital of France?") is False


def test_dynamic_filter_code_removal():
    # Ensure that code blocks are redacted
    input_text = "Here is some code: ```print('Hello')```"
    filtered = dynamic_filter(input_text)
    assert "CODE REMOVED" in filtered


def test_validate_request_success():
    data = {"message": "Hello"}
    message = validate_request(data)
    assert message == "Hello"


def test_validate_request_failure():
    data = {"message": ""}
    with pytest.raises(ValueError, match="Message is required"):
        validate_request(data)

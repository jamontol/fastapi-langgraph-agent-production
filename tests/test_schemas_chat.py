"""Unit tests for app.schemas.chat."""

import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, Message, SessionTitle


class TestMessage:
    """Tests for the Message schema."""

    def test_valid_message(self):
        """A valid message parses correctly."""
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_rejects_script_tags(self):
        """Script tags raise a validation error."""
        with pytest.raises(ValidationError):
            Message(role="user", content='<script>alert("x")</script>')

    def test_rejects_null_bytes(self):
        """Null bytes raise a validation error."""
        with pytest.raises(ValidationError):
            Message(role="user", content="a\0b")

    def test_rejects_unknown_role(self):
        """Unknown roles raise a validation error."""
        with pytest.raises(ValidationError):
            Message(role="admin", content="hi")

    def test_rejects_empty_content(self):
        """Empty content raises a validation error."""
        with pytest.raises(ValidationError):
            Message(role="user", content="")

    def test_ignores_extra_fields(self):
        """Extra fields are ignored."""
        msg = Message(role="user", content="hi", extra="ignored")
        assert msg.model_dump() == {"role": "user", "content": "hi"}


class TestChatRequest:
    """Tests for the ChatRequest schema."""

    def test_requires_at_least_one_message(self):
        """An empty message list raises a validation error."""
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])

    def test_valid_request(self):
        """A request with one message parses correctly."""
        request = ChatRequest(messages=[Message(role="user", content="hi")])
        assert len(request.messages) == 1


class TestSessionTitle:
    """Tests for the SessionTitle schema."""

    def test_normalizes_whitespace_and_punctuation(self):
        """Whitespace and surrounding punctuation are stripped."""
        assert SessionTitle(title="  Hello   World!  ").title == "Hello World"

    def test_rejects_empty_after_normalization(self):
        """A title that normalizes to empty raises a validation error."""
        with pytest.raises(ValidationError):
            SessionTitle(title="   !!!   ")

    def test_rejects_too_long(self):
        """An over-length title raises a validation error."""
        with pytest.raises(ValidationError):
            SessionTitle(title="x" * 61)

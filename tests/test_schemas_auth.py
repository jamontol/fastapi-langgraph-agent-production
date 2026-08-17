"""Unit tests for app.schemas.auth."""

import pytest
from pydantic import ValidationError

from app.schemas.auth import SessionResponse, UserCreate


class TestUserCreate:
    """Tests for the UserCreate schema."""

    def test_valid_user(self):
        """A valid user parses correctly."""
        user = UserCreate(email="user@example.com", password="StrongPass1!")
        assert user.email == "user@example.com"

    @pytest.mark.parametrize(
        "password",
        ["Aa1!", "nocaps1!", "NOCAPS1!", "NoSpecial1", "NoNumberA!"],
    )
    def test_rejects_weak_passwords(self, password):
        """Weak passwords raise a validation error."""
        with pytest.raises(ValidationError):
            UserCreate(email="user@example.com", password=password)

    def test_rejects_invalid_email(self):
        """An invalid email raises a validation error."""
        with pytest.raises(ValidationError):
            UserCreate(email="not-an-email", password="StrongPass1!")  # pragma: whitelist secret


class TestSessionResponse:
    """Tests for the SessionResponse schema."""

    def test_sanitizes_name(self):
        """Potentially harmful characters are stripped from the name."""
        session = SessionResponse(
            session_id="abc",
            name='foo <script> {"bad": true} `x`',
            token={"access_token": "tok", "token_type": "bearer", "expires_at": "2026-01-01T00:00:00Z"},
        )
        assert "(script)" not in session.name
        assert '"bad"' not in session.name
        assert "`x`" not in session.name

    def test_default_name_is_empty(self):
        """Missing name defaults to an empty string."""
        session = SessionResponse(
            session_id="abc",
            token={"access_token": "tok", "token_type": "bearer", "expires_at": "2026-01-01T00:00:00Z"},
        )
        assert session.name == ""

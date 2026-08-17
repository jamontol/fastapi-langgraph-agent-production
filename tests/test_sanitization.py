"""Unit tests for app.utils.sanitization."""

import pytest

from app.utils.sanitization import (
    sanitize_dict,
    sanitize_email,
    sanitize_list,
    sanitize_string,
    validate_password_strength,
)


class TestSanitizeString:
    """Tests for sanitize_string."""

    def test_escapes_html(self):
        """HTML input is escaped."""
        assert sanitize_string("<b>hi</b>") == "&lt;b&gt;hi&lt;/b&gt;"

    def test_removes_script_tags(self):
        """Script tags are stripped."""
        assert sanitize_string('<script>alert("x")</script>hello') == "hello"

    def test_removes_null_bytes(self):
        """Null bytes are removed."""
        assert sanitize_string("a\0b") == "ab"

    def test_converts_non_string(self):
        """Non-string input is converted to string."""
        assert sanitize_string(42) == "42"


class TestSanitizeEmail:
    """Tests for sanitize_email."""

    def test_lowercases_valid_email(self):
        """Valid email is lowercased."""
        assert sanitize_email("User@Example.COM") == "user@example.com"

    def test_rejects_invalid_email(self):
        """Invalid email raises ValueError."""
        with pytest.raises(ValueError):
            sanitize_email("not-an-email")


class TestSanitizeRecursive:
    """Tests for sanitize_dict and sanitize_list."""

    def test_dict_nested(self):
        """Nested dicts and lists are sanitized recursively."""
        result = sanitize_dict({"a": "<script>x</script>", "b": {"c": "<b>y</b>"}, "d": ["<i>z</i>"]})
        assert result == {"a": "", "b": {"c": "&lt;b&gt;y&lt;/b&gt;"}, "d": ["&lt;i&gt;z&lt;/i&gt;"]}

    def test_list_nested(self):
        """Nested dicts and lists are sanitized recursively."""
        assert sanitize_list(["<b>a</b>", {"k": "<i>b</i>"}, [42]]) == [
            "&lt;b&gt;a&lt;/b&gt;",
            {"k": "&lt;i&gt;b&lt;/i&gt;"},
            [42],
        ]


class TestValidatePasswordStrength:
    """Tests for validate_password_strength."""

    def test_valid_password(self):
        """Strong password returns True."""
        assert validate_password_strength("StrongPass1!") is True

    @pytest.mark.parametrize(
        "password",
        ["Aa1!", "nocaps1!", "NOCAPS1!", "NoSpecial1", "NoNumberA!"],
    )
    def test_invalid_passwords(self, password):
        """Weak passwords raise ValueError."""
        with pytest.raises(ValueError):
            validate_password_strength(password)

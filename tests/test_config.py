"""Unit tests for app.core.config helpers."""

import pytest

from app.core.config import (
    Environment,
    get_environment,
    parse_dict_of_lists_from_env,
    parse_list_from_env,
)


def test_get_environment_default(monkeypatch):
    """Missing APP_ENV resolves to development."""
    monkeypatch.delenv("APP_ENV", raising=False)
    assert get_environment() == Environment.DEVELOPMENT


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("production", Environment.PRODUCTION),
        ("prod", Environment.PRODUCTION),
        ("staging", Environment.STAGING),
        ("stage", Environment.STAGING),
        ("test", Environment.TEST),
    ],
)
def test_get_environment_overrides(monkeypatch, name, expected):
    """APP_ENV maps to the matching environment."""
    monkeypatch.setenv("APP_ENV", name)
    assert get_environment() == expected


def test_parse_list_from_env_comma_separated(monkeypatch):
    """Comma-separated values are split and stripped."""
    monkeypatch.setenv("TEST_KEY", "a, b ,c")
    assert parse_list_from_env("TEST_KEY") == ["a", "b", "c"]


def test_parse_list_from_env_single_value(monkeypatch):
    """A single value is returned as a one-item list."""
    monkeypatch.setenv("TEST_KEY", "a")
    assert parse_list_from_env("TEST_KEY") == ["a"]


def test_parse_list_from_env_missing(monkeypatch):
    """A missing variable falls back to the default."""
    monkeypatch.delenv("TEST_KEY", raising=False)
    assert parse_list_from_env("TEST_KEY", ["default"]) == ["default"]


def test_parse_dict_of_lists_from_env(monkeypatch):
    """Prefixed variables are grouped into a dict of lists."""
    monkeypatch.delenv("PREFIX_alpha", raising=False)
    monkeypatch.delenv("PREFIX_beta", raising=False)
    monkeypatch.setenv("PREFIX_alpha", "1,2")
    monkeypatch.setenv("PREFIX_beta", "3")
    assert parse_dict_of_lists_from_env("PREFIX_") == {"alpha": ["1", "2"], "beta": ["3"]}

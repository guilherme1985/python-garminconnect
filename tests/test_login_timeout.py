"""Tests for the login_timeout parameter (BUG-004)."""

import pytest

from garminconnect import Garmin, GarminConnectConnectionError


def test_login_timeout_accepts_positive_number() -> None:
    g = Garmin("test@example.com", "password", login_timeout=30.0)
    assert g.login_timeout == 30.0

    g2 = Garmin("test@example.com", "password", login_timeout=60)
    assert g2.login_timeout == 60


def test_login_timeout_none_is_default() -> None:
    g = Garmin("test@example.com", "password")
    assert g.login_timeout is None


def test_login_timeout_rejects_zero_or_negative() -> None:
    with pytest.raises(ValueError, match="login_timeout must be a positive"):
        Garmin("t@e.com", "p", login_timeout=0)
    with pytest.raises(ValueError, match="login_timeout must be a positive"):
        Garmin("t@e.com", "p", login_timeout=-5)


def test_login_timeout_rejects_non_number() -> None:
    with pytest.raises(ValueError, match="login_timeout must be a positive"):
        Garmin("t@e.com", "p", login_timeout="30")  # type: ignore[arg-type]


def test_login_timeout_rejects_bool() -> None:
    with pytest.raises(ValueError, match="login_timeout must be a positive"):
        Garmin("t@e.com", "p", login_timeout=True)  # type: ignore[arg-type]


def test_run_with_timeout_returns_result() -> None:
    from garminconnect import _run_with_timeout

    assert _run_with_timeout(lambda: 42, timeout=5.0) == 42


def test_run_with_timeout_raises_on_exceeded() -> None:
    import time

    from garminconnect import _run_with_timeout

    def slow_func() -> int:
        time.sleep(2.0)
        return 1

    with pytest.raises(GarminConnectConnectionError, match="exceeded timeout"):
        _run_with_timeout(slow_func, timeout=0.1)


def test_run_with_timeout_propagates_exception() -> None:
    from garminconnect import _run_with_timeout

    def boom() -> None:
        raise ValueError("kaboom")

    with pytest.raises(ValueError, match="kaboom"):
        _run_with_timeout(boom, timeout=5.0)


def test_login_with_timeout_aborts_slow_login(monkeypatch) -> None:
    """Verify login() respects login_timeout when the chain is slow."""
    import time

    g = Garmin("t@e.com", "p", login_timeout=0.1)

    def slow_impl(tokenstore=None):
        time.sleep(2.0)
        return None, None

    monkeypatch.setattr(g, "_login_impl", slow_impl)

    with pytest.raises(GarminConnectConnectionError, match="exceeded timeout"):
        g.login()


def test_login_without_timeout_does_not_use_thread(monkeypatch) -> None:
    """When login_timeout is None, _login_impl runs directly in the calling thread."""
    g = Garmin("t@e.com", "p")  # login_timeout=None

    called_with = []

    def fake_impl(tokenstore=None):
        called_with.append(tokenstore)
        return None, None

    monkeypatch.setattr(g, "_login_impl", fake_impl)

    result = g.login("/tmp/tokens")
    assert result == (None, None)
    assert called_with == ["/tmp/tokens"]

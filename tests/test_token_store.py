"""Tests for garminconnect.auth.token.TokenStore."""

import base64
import json
from pathlib import Path

import pytest

from garminconnect.auth.token import TokenStore
from garminconnect.models.exceptions import GarminTokenError


@pytest.fixture
def sample_tokens() -> dict:
    return {
        "access_token": "fake_access_token",
        "refresh_token": "fake_refresh_token",
        "expires_at": 1_900_000_000,
    }


def test_load_from_path_valid(tmp_path: Path, sample_tokens: dict) -> None:
    token_file = tmp_path / "tokens.json"
    token_file.write_text(json.dumps(sample_tokens))

    store = TokenStore()
    store.load_from_path(token_file)

    assert store.is_loaded
    assert store.access_token == "fake_access_token"
    assert store.refresh_token == "fake_refresh_token"
    assert store.expires_at == 1_900_000_000


def test_load_from_path_missing_file_raises(tmp_path: Path) -> None:
    store = TokenStore()
    with pytest.raises(GarminTokenError, match="Failed to read"):
        store.load_from_path(tmp_path / "does_not_exist.json")


def test_load_from_path_invalid_json_raises(tmp_path: Path) -> None:
    token_file = tmp_path / "bad.json"
    token_file.write_text("{this is not valid json")

    store = TokenStore()
    with pytest.raises(GarminTokenError, match="not valid JSON"):
        store.load_from_path(token_file)


def test_load_from_path_non_dict_raises(tmp_path: Path) -> None:
    token_file = tmp_path / "list.json"
    token_file.write_text("[1, 2, 3]")

    store = TokenStore()
    with pytest.raises(GarminTokenError, match="must be a JSON object"):
        store.load_from_path(token_file)


def test_load_from_base64_valid(sample_tokens: dict) -> None:
    encoded = base64.b64encode(json.dumps(sample_tokens).encode()).decode()
    store = TokenStore()
    store.load_from_base64(encoded)

    assert store.access_token == "fake_access_token"


def test_load_from_base64_invalid_b64_raises() -> None:
    store = TokenStore()
    with pytest.raises(GarminTokenError, match="Invalid base64"):
        store.load_from_base64("not!valid!base64!@#$")


def test_load_from_base64_invalid_json_raises() -> None:
    # valid base64, but the decoded payload is not JSON
    encoded = base64.b64encode(b"not json content here").decode()
    store = TokenStore()
    with pytest.raises(GarminTokenError, match="not valid JSON"):
        store.load_from_base64(encoded)


def test_load_from_base64_non_string_raises() -> None:
    store = TokenStore()
    with pytest.raises(GarminTokenError, match="must be a string"):
        store.load_from_base64(12345)  # type: ignore[arg-type]


def test_dump_creates_file_with_correct_permissions(
    tmp_path: Path, sample_tokens: dict
) -> None:
    import os

    store = TokenStore()
    store.data = sample_tokens

    target = tmp_path / "out.json"
    written = store.dump(target)

    assert written == target
    assert target.exists()
    assert json.loads(target.read_text()) == sample_tokens

    # Unix-only permission check
    if os.name != "nt":
        mode = target.stat().st_mode & 0o777
        assert mode == 0o600


def test_dump_uses_path_from_load(tmp_path: Path, sample_tokens: dict) -> None:
    token_file = tmp_path / "tokens.json"
    token_file.write_text(json.dumps(sample_tokens))

    store = TokenStore()
    store.load_from_path(token_file)
    store.data["access_token"] = "updated_token"

    store.dump()  # No arg — should use path from load

    reloaded = json.loads(token_file.read_text())
    assert reloaded["access_token"] == "updated_token"


def test_dump_without_path_raises(sample_tokens: dict) -> None:
    store = TokenStore()
    store.data = sample_tokens
    with pytest.raises(GarminTokenError, match="No destination path"):
        store.dump()


def test_clear_empties_data(sample_tokens: dict) -> None:
    store = TokenStore()
    store.data = sample_tokens
    assert store.is_loaded

    store.clear()
    assert not store.is_loaded
    assert store.access_token is None


def test_is_expiring_soon_with_no_expiry_returns_true() -> None:
    store = TokenStore()
    store.data = {"access_token": "x"}
    assert store.is_expiring_soon() is True


def test_is_expiring_soon_with_future_expiry_returns_false() -> None:
    import time

    store = TokenStore()
    store.data = {"access_token": "x", "expires_at": int(time.time()) + 3600}
    assert store.is_expiring_soon(threshold_seconds=300) is False


def test_is_expiring_soon_with_near_expiry_returns_true() -> None:
    import time

    store = TokenStore()
    store.data = {"access_token": "x", "expires_at": int(time.time()) + 100}
    assert store.is_expiring_soon(threshold_seconds=300) is True


def test_check_permissions_warns_for_too_open(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        pytest.skip("Permission check is unix-only")

    f = tmp_path / "bad_perms.json"
    f.write_text("{}")
    f.chmod(0o644)  # too open

    assert TokenStore.check_permissions(f) is False


def test_repr_shows_state(sample_tokens: dict) -> None:
    store = TokenStore()
    assert "empty" in repr(store)

    store.data = sample_tokens
    assert "loaded" in repr(store)

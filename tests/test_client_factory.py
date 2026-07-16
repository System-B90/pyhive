"""
Name: test_client_factory.py
Purpose: Unit tests for CLI credential resolution priority and OS-keyring caching.
"""

from typing import Any

import pytest

from pyhive.cli import client_factory
from pyhive.cli.state import CLIState


class FakeKeyring:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, account: str) -> str | None:
        return self._store.get((service, account))

    def set_password(self, service: str, account: str, value: str) -> None:
        self._store[(service, account)] = value


class FakeClient:
    """Stand-in for HiveClient that records how it was constructed."""

    last_call: dict[str, Any] | None = None

    def __init__(self, access_token: str, refresh_token: str = "") -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    @classmethod
    def _record(cls, method: str, **kwargs: Any) -> "FakeClient":
        cls.last_call = {"method": method, **kwargs}
        return cls(access_token=kwargs.get("api_token") or "pw-access", refresh_token="")

    def __call__(self, *args: Any, **kwargs: Any) -> "FakeClient":  # pragma: no cover
        raise NotImplementedError


@pytest.fixture(autouse=True)
def fake_keyring(monkeypatch):
    fake = FakeKeyring()
    monkeypatch.setattr(client_factory, "keyring", fake)
    return fake


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    fresh = CLIState()
    monkeypatch.setattr(client_factory, "state", fresh)
    return fresh


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("HIVE_ACCESS_TOKEN", raising=False)


def _patch_hive_client(monkeypatch):
    calls: dict[str, Any] = {}

    class StubHiveClient:
        def __init__(self, *, username: str, password: str, **kwargs: Any) -> None:
            calls["method"] = "password"
            calls["username"] = username
            calls["password"] = password
            self._access_token = "pw-access"
            self._refresh_token = "pw-refresh"

        @classmethod
        def from_api_token(cls, *, api_token: str, **kwargs: Any) -> "StubHiveClient":
            calls["method"] = "from_api_token"
            calls["api_token"] = api_token
            calls["refresh_token"] = kwargs.get("refresh_token")
            calls["auth_strategy"] = kwargs.get("auth_strategy")
            instance = cls.__new__(cls)
            instance._access_token = api_token
            instance._refresh_token = kwargs.get("refresh_token") or ""
            return instance

        @classmethod
        def from_sso(cls, **kwargs: Any) -> "StubHiveClient":
            calls["method"] = "from_sso"
            instance = cls.__new__(cls)
            instance._access_token = "sso-access"
            instance._refresh_token = "sso-refresh"
            return instance

    monkeypatch.setattr(client_factory, "HiveClient", StubHiveClient)
    return calls


def test_username_password_takes_priority(monkeypatch, fresh_state):
    calls = _patch_hive_client(monkeypatch)
    fresh_state.username = "bob"
    fresh_state.password = "secret"
    fresh_state.access_token = "ignored-token"

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "password"


def test_explicit_token_overrides_env_and_keyring(monkeypatch, fresh_state, fake_keyring):
    calls = _patch_hive_client(monkeypatch)
    fresh_state.access_token = "explicit-token"
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE, client_factory.KEYRING_ACCOUNT, "cached-access"
    )
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE,
        client_factory.KEYRING_REFRESH_ACCOUNT,
        "cached-refresh",
    )
    monkeypatch.setenv("HIVE_ACCESS_TOKEN", "env-token")

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "from_api_token"
    assert calls["api_token"] == "explicit-token"


def test_env_token_overrides_keyring(monkeypatch, fresh_state, fake_keyring):
    calls = _patch_hive_client(monkeypatch)
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE, client_factory.KEYRING_ACCOUNT, "cached-access"
    )
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE,
        client_factory.KEYRING_REFRESH_ACCOUNT,
        "cached-refresh",
    )
    monkeypatch.setenv("HIVE_ACCESS_TOKEN", "env-token")

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "from_api_token"
    assert calls["api_token"] == "env-token"
    assert calls["auth_strategy"] is None


def test_cached_tokens_used_with_cache_auth_strategy(monkeypatch, fresh_state, fake_keyring):
    calls = _patch_hive_client(monkeypatch)
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE, client_factory.KEYRING_ACCOUNT, "cached-access"
    )
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE,
        client_factory.KEYRING_REFRESH_ACCOUNT,
        "cached-refresh",
    )

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "from_api_token"
    assert calls["api_token"] == "cached-access"
    assert calls["refresh_token"] == "cached-refresh"
    assert calls["auth_strategy"] == "cache"


def test_missing_refresh_token_falls_back_to_sso(monkeypatch, fresh_state, fake_keyring):
    """A cached access token with no matching refresh token cannot support
    the 'cache' auth strategy, so we must not hand it to from_api_token
    without a refresh token (which would silently degrade to token_only)."""
    calls = _patch_hive_client(monkeypatch)
    fake_keyring.set_password(
        client_factory.KEYRING_SERVICE, client_factory.KEYRING_ACCOUNT, "cached-access"
    )

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "from_sso"


def test_no_credentials_falls_back_to_sso(monkeypatch, fresh_state):
    calls = _patch_hive_client(monkeypatch)

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "from_sso"


def test_cache_token_flag_stores_access_and_refresh_tokens(
    monkeypatch, fresh_state, fake_keyring
):
    _patch_hive_client(monkeypatch)
    fresh_state.cache_token = True

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert (
        fake_keyring.get_password(client_factory.KEYRING_SERVICE, client_factory.KEYRING_ACCOUNT)
        == "sso-access"
    )
    assert (
        fake_keyring.get_password(
            client_factory.KEYRING_SERVICE, client_factory.KEYRING_REFRESH_ACCOUNT
        )
        == "sso-refresh"
    )


def test_cache_token_flag_off_does_not_store(monkeypatch, fresh_state, fake_keyring):
    _patch_hive_client(monkeypatch)
    fresh_state.cache_token = False

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert (
        fake_keyring.get_password(client_factory.KEYRING_SERVICE, client_factory.KEYRING_ACCOUNT)
        is None
    )


def test_keyring_read_errors_are_swallowed(monkeypatch, fresh_state):
    calls = _patch_hive_client(monkeypatch)

    class BrokenKeyring:
        def get_password(self, service: str, account: str) -> str | None:
            raise RuntimeError("keychain locked")

        def set_password(self, service: str, account: str, value: str) -> None:
            raise RuntimeError("keychain locked")

    monkeypatch.setattr(client_factory, "keyring", BrokenKeyring())

    client_factory.get_hive_client("https://hive.org", verify=False)

    assert calls["method"] == "from_sso"


def test_keyring_write_errors_do_not_crash(monkeypatch, fresh_state):
    _patch_hive_client(monkeypatch)
    fresh_state.cache_token = True

    class WriteFailsKeyring:
        def get_password(self, service: str, account: str) -> str | None:
            return None

        def set_password(self, service: str, account: str, value: str) -> None:
            raise RuntimeError("keychain locked")

    monkeypatch.setattr(client_factory, "keyring", WriteFailsKeyring())

    client_factory.get_hive_client("https://hive.org", verify=False)

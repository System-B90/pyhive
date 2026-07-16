"""
Name: test_authenticated_hive_client.py
Purpose: Unit tests for authentication strategies and token refresh/caching behavior.
"""

import pytest

from pyhive.src.authenticated_hive_client import AuthenticatedHiveClient

HIVE_URL = "https://hive.example.com"


def _client(**kwargs: object) -> AuthenticatedHiveClient:
    return AuthenticatedHiveClient(
        username=kwargs.pop("username", "user"),  # type: ignore[arg-type]
        password=kwargs.pop("password", "pass"),  # type: ignore[arg-type]
        hive_url=HIVE_URL,
        proxy=None,
        **kwargs,
    )


def test_password_login_sets_tokens(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/token/",
        json={"access": "access-1", "refresh": "refresh-1"},
        status_code=200,
    )

    client = _client()

    assert client._auth_strategy == "password"
    assert client._access_token == "access-1"
    assert client._refresh_token == "refresh-1"
    assert client._session.headers["Authorization"] == "Bearer access-1"


def test_token_only_strategy_has_no_refresh_token(httpx_mock):
    client = _client(existing_token="tok-only")

    assert client._auth_strategy == "token_only"
    assert client._refresh_token == ""
    assert client._session.headers["Authorization"] == "Bearer tok-only"


def test_token_only_refresh_raises(httpx_mock):
    client = _client(existing_token="tok-only")

    with pytest.raises(RuntimeError, match="Cannot refresh access token"):
        client._refresh_access_token()


def test_sso_strategy_requires_refresh_token(httpx_mock):
    with pytest.raises(AssertionError, match="no refresh token was given"):
        _client(existing_token="tok", auth_strategy="sso", refresh_token=None)


@pytest.mark.parametrize("strategy", ["sso", "cache"])
def test_sso_and_cache_strategy_refresh(httpx_mock, strategy):
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/token/refresh/",
        json={"access": "access-2", "refresh": "refresh-2"},
        status_code=200,
    )

    client = _client(
        existing_token="access-1",
        auth_strategy=strategy,
        refresh_token="refresh-1",
    )
    assert client._auth_strategy == strategy

    client._refresh_access_token()

    assert client._access_token == "access-2"
    assert client._refresh_token == "refresh-2"
    assert client._session.headers["Authorization"] == "Bearer access-2"


def test_get_refreshes_once_on_401_then_succeeds(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{HIVE_URL}/api/foo",
        status_code=401,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/token/refresh/",
        json={"access": "access-2", "refresh": "refresh-2"},
        status_code=200,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{HIVE_URL}/api/foo",
        json={"ok": True},
        status_code=200,
    )

    client = _client(
        existing_token="access-1", auth_strategy="cache", refresh_token="refresh-1"
    )

    result = client.get("/api/foo")

    assert result == {"ok": True}
    assert client._access_token == "access-2"


def test_get_token_only_raises_on_401_instead_of_looping(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{HIVE_URL}/api/foo", status_code=401)

    client = _client(existing_token="access-1")

    with pytest.raises(RuntimeError, match="Cannot refresh access token"):
        client.get("/api/foo")


def test_retry_on_bad_gateway_then_success(httpx_mock, monkeypatch):
    monkeypatch.setattr("pyhive.src.authenticated_hive_client.time.sleep", lambda _: None)

    httpx_mock.add_response(method="GET", url=f"{HIVE_URL}/api/foo", status_code=502)
    httpx_mock.add_response(
        method="GET", url=f"{HIVE_URL}/api/foo", json={"ok": True}, status_code=200
    )

    client = _client(existing_token="access-1")

    result = client.get("/api/foo")

    assert result == {"ok": True}


def test_post_raises_value_error_with_json_body_on_400(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/foo",
        json={"detail": "bad input"},
        status_code=400,
    )

    client = _client(existing_token="access-1")

    with pytest.raises(ValueError, match="bad input"):
        client.post("/api/foo", {"a": 1})

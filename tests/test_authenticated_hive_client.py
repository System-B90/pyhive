"""
Name: test_authenticated_hive_client.py
Purpose: Unit tests for authentication strategies and token refresh/caching behavior.
"""

import pytest
from httpx import HTTPStatusError

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
    monkeypatch.setattr(
        "pyhive.src.authenticated_hive_client.time.sleep", lambda _: None
    )

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


def test_retry_on_bad_gateway_exhausts_and_raises(httpx_mock, monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr(
        "pyhive.src.authenticated_hive_client.time.sleep", sleeps.append
    )

    for _ in range(5):
        httpx_mock.add_response(
            method="GET", url=f"{HIVE_URL}/api/foo", status_code=502
        )

    client = _client(existing_token="access-1")

    with pytest.raises(HTTPStatusError):
        client.get("/api/foo")

    assert sleeps == [0.5, 1.0, 2.0, 4.0]


def test_refresh_endpoint_failure_propagates(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/token/refresh/",
        status_code=401,
    )

    client = _client(
        existing_token="access-1", auth_strategy="cache", refresh_token="refresh-1"
    )

    with pytest.raises(HTTPStatusError):
        client._refresh_access_token()


def test_delete_204_succeeds(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{HIVE_URL}/api/foo/1", status_code=204
    )

    client = _client(existing_token="access-1")

    client.delete("/api/foo/1")


def test_delete_non_204_raises_runtime_error(httpx_mock):
    httpx_mock.add_response(
        method="DELETE", url=f"{HIVE_URL}/api/foo/1", status_code=200
    )

    client = _client(existing_token="access-1")

    with pytest.raises(RuntimeError, match="Failed to delete"):
        client.delete("/api/foo/1")


def test_put_returns_json_object(httpx_mock):
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/foo/1", json={"id": 1}, status_code=200
    )

    client = _client(existing_token="access-1")

    result = client.put("/api/foo/1", {"name": "x"})

    assert result == {"id": 1}


def test_put_non_dict_json_raises_type_error(httpx_mock):
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/foo/1", json=[1, 2, 3], status_code=200
    )

    client = _client(existing_token="access-1")

    with pytest.raises(TypeError, match="Expected JSON object"):
        client.put("/api/foo/1", {"name": "x"})


def test_patch_returns_json_object(httpx_mock):
    httpx_mock.add_response(
        method="PATCH", url=f"{HIVE_URL}/api/foo/1", json={"id": 1}, status_code=200
    )

    client = _client(existing_token="access-1")

    result = client.patch("/api/foo/1", {"name": "x"})

    assert result == {"id": 1}


def test_get_scalar_json_raises_type_error(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{HIVE_URL}/api/foo", json=42, status_code=200
    )

    client = _client(existing_token="access-1")

    with pytest.raises(TypeError, match="Expected JSON object or list"):
        client.get("/api/foo")


def test_get_list_json_passes_through(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{HIVE_URL}/api/foo", json=[1, 2], status_code=200
    )

    client = _client(existing_token="access-1")

    assert client.get("/api/foo") == [1, 2]


def test_post_400_non_json_body_falls_back_to_text(httpx_mock):
    """A non-JSON 400 body reaches the caller as text, not a decode error.

    Proxies, gateways and nginx answer 400 with an HTML page, a plain-text
    message or nothing at all. The decorator used to interpolate
    ``response.json()`` directly into the HTTPStatusError message, so the
    decode blew up *before* the HTTPStatusError existed; post() could not
    catch it and the caller got a bare JSONDecodeError naming neither the
    status nor the endpoint.
    """
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/foo",
        content=b"not json",
        status_code=400,
        headers={"content-type": "text/plain"},
    )

    client = _client(existing_token="access-1")

    with pytest.raises(ValueError, match="HTTP 400 Error: not json"):
        client.post("/api/foo", {"a": 1})


def test_post_400_empty_body_reports_the_status(httpx_mock):
    """An empty 400 body is the other shape that used to fail to decode."""
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/foo",
        content=b"",
        status_code=400,
    )

    client = _client(existing_token="access-1")

    with pytest.raises(ValueError, match="HTTP 400 Error:"):
        client.post("/api/foo", {"a": 1})


def test_post_400_non_json_body_does_not_leak_decode_error(httpx_mock):
    """Whatever escapes post() must not be a JSONDecodeError."""
    import json

    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/foo",
        content=b"<html>gateway said no</html>",
        status_code=400,
        headers={"content-type": "text/html"},
    )

    client = _client(existing_token="access-1")

    with pytest.raises(ValueError) as excinfo:
        client.post("/api/foo", {"a": 1})

    assert not isinstance(excinfo.value, json.JSONDecodeError)
    assert "gateway said no" in str(excinfo.value)

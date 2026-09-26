"""
Name: test_sso_utils.py
Purpose: Unit tests for PyHive SSO utilities.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from pyhive.client.sso_utils import (
    _exchange_code_for_token,
    _generate_pkce_pair,
    get_sso_token,
)


def test_generate_pkce_pair():
    verifier, challenge = _generate_pkce_pair()
    assert len(verifier) == 86
    assert len(challenge) > 0


def test_exchange_code_for_token_success(httpx_mock):
    hive_url = "https://hive.example.com"
    mock_timestamp = 1711756800  # 2024-03-30 00:00:00 timezone.utc

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/token/",
        json={"access_token": "opaque_dot_token_123", "id_token": "mock_id_token"},
        status_code=200,
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/exchange/",
        json={
            "access_token": "jwt_simplejwt_123",
            "refresh_token": "mock_refresh",
            "expires_at": mock_timestamp,
        },
        status_code=200,
    )

    access, refresh, expires = _exchange_code_for_token(
        hive_url, "code123", "verifier123"
    )

    assert access == "jwt_simplejwt_123"
    assert refresh == "mock_refresh"
    assert expires == datetime.fromtimestamp(mock_timestamp, tz=timezone.utc)


def test_exchange_code_for_token_missing_opaque_token(httpx_mock):
    hive_url = "https://hive.example.com"

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/token/",
        json={"id_token": "mock_id_token"},
        status_code=200,
    )

    with pytest.raises(ValueError, match="did not contain an 'access_token'"):
        _exchange_code_for_token(hive_url, "code123", "verifier123")


def test_exchange_code_for_token_missing_jwt_data(httpx_mock):
    hive_url = "https://hive.example.com"

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/token/",
        json={"access_token": "opaque_dot_token_123"},
        status_code=200,
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/exchange/",
        json={"refresh_token": "mock_refresh"},
        status_code=200,
    )

    with pytest.raises(ValueError, match="Exchange response is missing"):
        _exchange_code_for_token(hive_url, "code123", "verifier123")


def test_exchange_code_for_token_http_error(httpx_mock):
    hive_url = "https://hive.example.com"

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/token/",
        status_code=401,
        text="Unauthorized Client",
    )

    with pytest.raises(RuntimeError, match=r"Token exchange failed \(HTTP 401\)"):
        _exchange_code_for_token(hive_url, "code123", "verifier123")


def test_exchange_code_for_token_exchange_http_error(httpx_mock):
    hive_url = "https://hive.example.com"

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/token/",
        json={"access_token": "opaque_dot_token_123"},
        status_code=200,
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/exchange/",
        status_code=403,
        text="Forbidden",
    )

    with pytest.raises(RuntimeError, match=r"SSO Token Exchange failed \(HTTP 403\)"):
        _exchange_code_for_token(hive_url, "code123", "verifier123")


@patch("pyhive.client.sso_utils.webbrowser.open")
@patch("pyhive.client.sso_utils._start_local_callback_server")
def test_get_sso_token_orchestration(mock_server, mock_browser):
    hive_url = "https://hive.example.com"
    mock_dt = datetime(2026, 3, 29, tzinfo=timezone.utc)
    mock_server.return_value = ("access_123", "refresh_123", mock_dt)

    access, refresh, expires = get_sso_token(hive_url)

    assert access == "access_123"
    assert refresh == "refresh_123"
    assert expires == mock_dt
    mock_browser.assert_called_once()
    assert "code_challenge" in mock_browser.call_args[0][0]

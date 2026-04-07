"""
Name: test_sso_utils.py
Purpose: Unit tests for PyHive SSO utilities.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import pytest
from unittest.mock import patch
from pyhive.client.sso_utils import (
    _generate_pkce_pair,
    _exchange_code_for_token,
    get_sso_token,
)


def test_generate_pkce_pair():
    verifier, challenge = _generate_pkce_pair()
    assert len(verifier) == 86
    assert len(challenge) > 0


def test_exchange_code_for_token_success(httpx_mock):
    hive_url = "https://hive.example.com"

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/token/",
        json={"access_token": "opaque_dot_token_123", "id_token": "mock_id_token"},
        status_code=200,
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/api/core/sso/exchange/",
        json={"access_token": "jwt_simplejwt_123", "refresh_token": "mock_refresh"},
        status_code=200,
    )

    token = _exchange_code_for_token(hive_url, "code123", "verifier123")
    assert token == "jwt_simplejwt_123"


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


def test_exchange_code_for_token_missing_jwt_token(httpx_mock):
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

    with pytest.raises(ValueError, match="did not contain a valid JWT 'access_token'"):
        _exchange_code_for_token(hive_url, "code123", "verifier123")


@patch("pyhive.client.sso_utils.webbrowser.open")
@patch("pyhive.client.sso_utils._start_local_callback_server")
def test_get_sso_token_orchestration(mock_server, mock_browser):
    hive_url = "https://hive.example.com"
    mock_server.return_value = "final_token"

    token = get_sso_token(hive_url)

    assert token == "final_token"
    mock_browser.assert_called_once()
    assert "code_challenge" in mock_browser.call_args[0][0]

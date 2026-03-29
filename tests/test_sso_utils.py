"""
Name: test_sso_utils.py
Purpose: Unit tests for PyHive SSO utilities.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import base64
import json
import pytest
from unittest.mock import patch
from pyhive.client.sso_utils import (
    _decode_jwt_payload,
    _generate_pkce_pair,
    _exchange_code_for_token,
    get_sso_token,
)


def test_decode_jwt_payload_valid():
    payload = {"sub": "123", "api_token": "test_token"}
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    assert _decode_jwt_payload(f"a.{payload_b64}.b")["api_token"] == "test_token"


def test_generate_pkce_pair():
    verifier, challenge = _generate_pkce_pair()
    assert len(verifier) == 86
    assert len(challenge) > 0


def test_exchange_code_for_token_success(httpx_mock):
    hive_url = "https://hive.example.com"
    id_payload = (
        base64.urlsafe_b64encode(json.dumps({"api_token": "sk_123"}).encode())
        .decode()
        .rstrip("=")
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/sso/token/",
        json={"id_token": f"a.{id_payload}.b"},
        status_code=200,
    )

    token = _exchange_code_for_token(hive_url, "code123", "verifier123")
    assert token == "sk_123"


def test_exchange_code_for_token_missing_claim(httpx_mock):
    hive_url = "https://hive.example.com"
    id_payload = (
        base64.urlsafe_b64encode(json.dumps({"sub": "user"}).encode())
        .decode()
        .rstrip("=")
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{hive_url}/sso/token/",
        json={"id_token": f"a.{id_payload}.b"},
        status_code=200,
    )

    with pytest.raises(ValueError, match="does not contain the 'api_token' claim"):
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

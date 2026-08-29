"""
Name: test_system.py
Purpose: Offline unit tests for SystemClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient

HIVE_URL = "https://hive.example.com"


def _client(httpx_mock: Any) -> HiveClient:
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/token/",
        json={"access": "access-1", "refresh": "refresh-1"},
        status_code=200,
    )
    return HiveClient(
        "user", "pass", HIVE_URL, verify=False, proxy=None, skip_version_check=True
    )


def test_get_server_time(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/time/", json="2026-01-01T00:00:00Z"
    )
    assert client.get_server_time() == "2026-01-01T00:00:00Z"


def test_get_powersync_token(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/powersync/token/",
        json={"token": "t", "endpoint": "e", "expiresAt": 1798761600},
    )
    token = client.get_powersync_token()
    assert token.token == "t"

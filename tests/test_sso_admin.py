"""
Name: test_sso_admin.py
Purpose: Offline unit tests for SsoAdminClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.sso_application import SsoApplication

HIVE_URL = "https://hive.example.com"

SSO_APPLICATION = {"id": 1, "name": "App"}


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


def test_get_sso_applications(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/sso/applications/", json=[SSO_APPLICATION]
    )
    apps = list(client.get_sso_applications())
    assert apps == [SsoApplication.from_dict(SSO_APPLICATION, hive_client=client)]


def test_get_sso_application(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/sso/applications/1/", json=SSO_APPLICATION
    )
    app = client.get_sso_application(1)
    assert isinstance(app, SsoApplication)


def test_create_sso_application(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/sso/applications/",
        json=SSO_APPLICATION,
    )
    app = client.create_sso_application("App")
    assert isinstance(app, SsoApplication)


def test_update_sso_application(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/sso/applications/1/",
        json=SSO_APPLICATION,
    )
    app = SsoApplication.from_dict(SSO_APPLICATION, hive_client=client)
    updated = client.update_sso_application(app, name="App2")
    assert isinstance(updated, SsoApplication)


def test_delete_sso_application(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/sso/applications/1/",
        status_code=204,
    )
    client.delete_sso_application(1)


def test_get_client_info(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/sso/client-info/?client_id=abc",
        json={"name": "App", "scopes": {}},
    )
    info = client.get_client_info("abc")
    assert info.name == "App"

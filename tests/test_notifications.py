"""
Name: test_notifications.py
Purpose: Offline unit tests for NotificationClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.notification import Notification

HIVE_URL = "https://hive.example.com"

NOTIFICATION = {
    "id": 1,
    "response_type": "Comment",
    "exercise_id": 1,
    "exercise_name": "Ex",
    "module_id": 1,
    "subject": 1,
    "program_id": 1,
    "help_type": None,
    "help_title": "",
    "from_user_id": None,
    "from_user_name": "System",
    "time": "2026-01-01T00:00:00Z",
    "for_user": 1,
    "for_user_name": "User",
}


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


def test_get_notifications(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(url=f"{HIVE_URL}/api/core/notification/", json=[NOTIFICATION])
    notifications = list(client.get_notifications())
    assert notifications == [Notification.from_dict(NOTIFICATION, hive_client=client)]


def test_get_notification(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/notification/1/", json=NOTIFICATION
    )
    notification = client.get_notification(1)
    assert isinstance(notification, Notification)


def test_create_notification(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{HIVE_URL}/api/core/notification/", json=NOTIFICATION
    )
    notification = client.create_notification(1)
    assert isinstance(notification, Notification)


def test_update_notification(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH", url=f"{HIVE_URL}/api/core/notification/1/", json=NOTIFICATION
    )
    notification = Notification.from_dict(NOTIFICATION, hive_client=client)
    updated = client.update_notification(notification, was_read=True)
    assert isinstance(updated, Notification)


def test_delete_notification(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE", url=f"{HIVE_URL}/api/core/notification/1/", status_code=204
    )
    client.delete_notification(1)

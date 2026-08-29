"""
Name: test_assignments.py
Purpose: Offline unit tests for the write/action endpoints added to
AssignmentClientMixin (update/patch/delete/lock/unlock/subscribe and the
latest-assignments notification feed), mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.assignment import Assignment
from pyhive.src.types.assignment_notification import AssignmentNotification

HIVE_URL = "https://hive.example.com"

ASSIGNMENT = {
    "id": 1,
    "user_id": 1,
    "checker_id": None,
    "is_subscribed": False,
    "exercise_id": 1,
    "assignment_status": "New",
    "patbas": False,
    "last_staff_updated": "2026-01-01T00:00:00Z",
    "work_time": 0,
    "notifications": [],
}
ASSIGNMENT_NOTIFICATION = {
    "id": 1,
    "user_id": 1,
    "user_name": "U",
    "exercise_id": 1,
    "module_id": 1,
    "subject": 1,
    "last_staff_updated": "2026-01-01T00:00:00Z",
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


def test_update_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/core/assignments/1/", json=ASSIGNMENT
    )
    assignment = Assignment.from_dict(ASSIGNMENT, hive_client=client)
    updated = client.update_assignment(assignment)
    assert isinstance(updated, Assignment)


def test_patch_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH", url=f"{HIVE_URL}/api/core/assignments/1/", json=ASSIGNMENT
    )
    result = client.patch_assignment(1, work_time=5)
    assert result.id == 1


def test_delete_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE", url=f"{HIVE_URL}/api/core/assignments/1/", status_code=204
    )
    client.delete_assignment(1)


def test_lock_unlock_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/core/assignments/1/lock/", json={}
    )
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/core/assignments/1/unlock/", json={}
    )
    client.lock_assignment(1)
    client.unlock_assignment(1)


def test_subscribe_unsubscribe_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/core/assignments/1/subscribe/", json={}
    )
    httpx_mock.add_response(
        method="PUT", url=f"{HIVE_URL}/api/core/assignments/1/unsubscribe/", json={}
    )
    client.subscribe_to_assignment(1)
    client.unsubscribe_from_assignment(1)


def test_get_latest_assignments(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/assignments/latest/", json=[ASSIGNMENT_NOTIFICATION]
    )
    notifications = list(client.get_latest_assignments())
    assert notifications == [
        AssignmentNotification.from_dict(ASSIGNMENT_NOTIFICATION, hive_client=client)
    ]


def test_create_latest_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/assignments/latest/",
        json=ASSIGNMENT_NOTIFICATION,
    )
    created = client.create_latest_assignment(user_id=1)
    assert isinstance(created, AssignmentNotification)


def test_update_latest_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/assignments/latest/1/",
        json=ASSIGNMENT_NOTIFICATION,
    )
    updated = client.update_latest_assignment(1, user_id=1)
    assert isinstance(updated, AssignmentNotification)


def test_delete_latest_assignment(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/assignments/latest/1/",
        status_code=204,
    )
    client.delete_latest_assignment(1)

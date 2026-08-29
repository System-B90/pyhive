"""
Name: test_seating.py
Purpose: Offline unit tests for SeatingClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.seating import Seating

HIVE_URL = "https://hive.example.com"

SEATING = {"id": 1, "classroom": 3, "x": 0, "y": 0}


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


def test_get_seatings(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/management/seating/", json=[SEATING]
    )
    seatings = list(client.get_seatings())
    assert seatings == [Seating.from_dict(SEATING, hive_client=client)]


def test_get_seating(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/management/seating/1/", json=SEATING
    )
    seating = client.get_seating(1)
    assert isinstance(seating, Seating)


def test_create_seating(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{HIVE_URL}/api/core/management/seating/", json=SEATING
    )
    seating = client.create_seating(3, 0, 0)
    assert isinstance(seating, Seating)


def test_update_seating(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH", url=f"{HIVE_URL}/api/core/management/seating/1/", json=SEATING
    )
    seating = Seating.from_dict(SEATING, hive_client=client)
    updated = client.update_seating(seating, x=1)
    assert isinstance(updated, Seating)


def test_delete_seating(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/management/seating/1/",
        status_code=204,
    )
    client.delete_seating(1)

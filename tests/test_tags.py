"""
Name: test_tags.py
Purpose: Offline unit tests for TagClientMixin, mocked via pytest-httpx.
"""

from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.tag import Tag

HIVE_URL = "https://hive.example.com"

TAG = {"id": 1, "name": "T", "color": "#000"}


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


def test_get_tags(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(url=f"{HIVE_URL}/api/core/tags/", json=[TAG])
    tags = list(client.get_tags())
    assert tags == [Tag.from_dict(TAG, hive_client=client)]


def test_get_tag(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(url=f"{HIVE_URL}/api/core/tags/1/", json=TAG)
    tag = client.get_tag(1)
    assert isinstance(tag, Tag)


def test_create_tag(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(method="POST", url=f"{HIVE_URL}/api/core/tags/", json=TAG)
    tag = client.create_tag("T", "#000")
    assert isinstance(tag, Tag)


def test_update_tag(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH", url=f"{HIVE_URL}/api/core/tags/1/", json=TAG
    )
    tag = Tag.from_dict(TAG, hive_client=client)
    updated = client.update_tag(tag, name="T2")
    assert isinstance(updated, Tag)


def test_delete_tag(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE", url=f"{HIVE_URL}/api/core/tags/1/", status_code=204
    )
    client.delete_tag(1)

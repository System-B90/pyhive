"""
Name: test_client_shared.py
Purpose: Unit tests for ClientCoreMixin._get_core_items (pagination, query-param
    normalization, malformed-payload handling) — offline, pytest-httpx only.
"""

from typing import Any, Self

import pytest

from pyhive.client import HiveClient
from pyhive.src.types.core_item import HiveCoreItem

HIVE_URL = "https://hive.example.com"


class _Item(HiveCoreItem):
    """Minimal HiveCoreItem stand-in so these tests don't depend on any real
    generated model shape."""

    id: int
    name: str

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        del hive_client
        return cls.model_validate(src_dict)


def _client(httpx_mock: Any, **kwargs: Any) -> HiveClient:
    del httpx_mock
    return HiveClient(
        "user",
        "pass",
        HIVE_URL,
        existing_token="tok",
        skip_version_check=True,
        **kwargs,
    )


def test_non_paginated_list_yields_typed_items(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{HIVE_URL}/api/foo/",
        json=[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}],
    )
    client = _client(httpx_mock)

    items = list(client._get_core_items("/api/foo/", _Item))

    assert [i.id for i in items] == [1, 2]
    assert all(isinstance(i, _Item) for i in items)


def test_non_paginated_empty_list_yields_nothing(httpx_mock):
    httpx_mock.add_response(method="GET", url=f"{HIVE_URL}/api/foo/", json=[])
    client = _client(httpx_mock)

    assert list(client._get_core_items("/api/foo/", _Item)) == []


def test_malformed_payload_raises_type_error(httpx_mock):
    httpx_mock.add_response(
        method="GET", url=f"{HIVE_URL}/api/foo/", json={"nope": True}
    )
    client = _client(httpx_mock)

    with pytest.raises(TypeError, match="neither paginated nor the results"):
        list(client._get_core_items("/api/foo/", _Item))


def test_multi_page_pagination_follows_next(httpx_mock):
    page1 = {
        "count": 3,
        "next": f"{HIVE_URL}/api/foo/?page=2",
        "previous": None,
        "results": [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}],
    }
    page2 = {
        "count": 3,
        "next": None,
        "previous": f"{HIVE_URL}/api/foo/?page=1",
        "results": [{"id": 3, "name": "c"}],
    }
    httpx_mock.add_response(method="GET", url=f"{HIVE_URL}/api/foo/", json=page1)
    httpx_mock.add_response(method="GET", url=f"{HIVE_URL}/api/foo/?page=2", json=page2)

    client = _client(httpx_mock)

    items = list(client._get_core_items("/api/foo/", _Item))

    assert [i.id for i in items] == [1, 2, 3]

    requests = httpx_mock.get_requests()
    assert requests[1].url == f"{HIVE_URL}/api/foo/?page=2"


def test_pagination_follow_up_request_allows_redirects(httpx_mock):
    page1 = {
        "count": 1,
        "next": f"{HIVE_URL}/api/foo/?page=2",
        "previous": None,
        "results": [{"id": 1, "name": "a"}],
    }
    page2 = {"count": 1, "next": None, "previous": None, "results": []}

    # A 302 redirect from the "next" URL to the real second page proves
    # follow_redirects=True is actually being passed through on that call.
    httpx_mock.add_response(method="GET", url=f"{HIVE_URL}/api/foo/", json=page1)
    httpx_mock.add_response(
        method="GET",
        url=f"{HIVE_URL}/api/foo/?page=2",
        status_code=302,
        headers={"location": f"{HIVE_URL}/api/foo/?page=2&rectified=1"},
    )
    httpx_mock.add_response(
        method="GET", url=f"{HIVE_URL}/api/foo/?page=2&rectified=1", json=page2
    )

    client = _client(httpx_mock)

    items = list(client._get_core_items("/api/foo/", _Item))

    assert [i.id for i in items] == [1]


def test_query_params_none_skipped_list_comma_joined_scalars_passthrough(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{HIVE_URL}/api/foo/?ids=1%2C2%2C3&name=bob",
        json=[],
    )
    client = _client(httpx_mock)

    list(
        client._get_core_items(
            "/api/foo/", _Item, ids=[1, 2, 3], name="bob", unused=None
        )
    )

    request = httpx_mock.get_requests()[0]
    assert dict(request.url.params) == {"ids": "1,2,3", "name": "bob"}

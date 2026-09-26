"""Hive < 7.3.0 serves integer ids for the lesson/schedule family; 7.3.0+ serves UUIDs."""

from typing import Any
from uuid import UUID, uuid4

import pytest

from pyhive.client import HiveClient
from pyhive.client.utils import resolve_item_or_uuid
from pyhive.src.types.event_tagging import EventTagging


def _client() -> HiveClient:
    return HiveClient(
        "user",
        "pass",
        "https://hive.example",
        existing_token="tok",
        skip_version_check=True,
    )


@pytest.mark.parametrize("item_id", [1, uuid4()])
def test_event_tagging_accepts_int_and_uuid_ids(item_id: Any) -> None:
    tagging = EventTagging.from_dict(
        {"id": item_id, "event_id": item_id, "tag_id": item_id}, _client()
    )
    assert tagging.id == tagging.event_id == tagging.tag_id == item_id


def test_resolve_item_or_uuid_keeps_int_ids() -> None:
    assert resolve_item_or_uuid(5) == 5
    assert resolve_item_or_uuid("5") == 5
    uid = uuid4()
    assert resolve_item_or_uuid(str(uid)) == uid
    assert isinstance(resolve_item_or_uuid(uid), UUID)

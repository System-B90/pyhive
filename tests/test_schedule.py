"""
Name: test_schedule.py
Purpose: Offline unit tests for ScheduleClientMixin, mocked via pytest-httpx.
"""

import datetime
from typing import Any

from pyhive.client import HiveClient
from pyhive.src.types.event_attendee import EventAttendee
from pyhive.src.types.event_category import EventCategory
from pyhive.src.types.event_instructor import EventInstructor
from pyhive.src.types.event_tag import EventTag
from pyhive.src.types.event_tagging import EventTagging
from pyhive.src.types.module import Module
from pyhive.src.types.schedule_event import ScheduleEvent

HIVE_URL = "https://hive.example.com"

EVENT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CATEGORY_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
TAG_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
TAGGING_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
ATTENDEE_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
INSTRUCTOR_LINK_ID = "ffffffff-ffff-4fff-8fff-ffffffffffff"

EVENT_CATEGORY = {"id": CATEGORY_ID, "name": "Cat", "color": "#fff"}
EVENT_ATTENDEE = {"id": ATTENDEE_ID, "event_id": EVENT_ID, "attendee_class_id": 2}
EVENT_INSTRUCTOR = {"id": INSTRUCTOR_LINK_ID, "event_id": EVENT_ID, "instructor_id": 2}
EVENT_TAG = {"id": TAG_ID, "name": "Tag", "color": "#000"}
EVENT_TAGGING = {"id": TAGGING_ID, "event_id": EVENT_ID, "tag_id": TAG_ID}
SCHEDULE_EVENT = {
    "id": EVENT_ID,
    "start": "2026-01-01T10:00:00Z",
    "end": "2026-01-01T11:00:00Z",
    "attendees": [],
    "color": "#fff",
    "category_name": "Cat",
}
MODULE = {
    "id": 1,
    "name": "Daily Review",
    "parent_subject_id": 1,
    "order": "0",
    "sync_status": "Normal",
    "parent_program_name": "Program",
    "parent_subject_name": "Subject",
    "parent_subject_symbol": "S",
    "segel_path": "",
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


def test_get_schedule_events(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/events/", json=[SCHEDULE_EVENT]
    )
    events = list(client.get_schedule_events())
    assert events == [ScheduleEvent.from_dict(SCHEDULE_EVENT, hive_client=client)]


def test_get_schedule_event(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/events/{EVENT_ID}/", json=SCHEDULE_EVENT
    )
    event = client.get_schedule_event(EVENT_ID)
    assert isinstance(event, ScheduleEvent)


def test_create_schedule_event(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{HIVE_URL}/api/core/schedule/events/", json=SCHEDULE_EVENT
    )
    event = client.create_schedule_event(
        datetime.datetime(2026, 1, 1, 10), datetime.datetime(2026, 1, 1, 11)
    )
    assert isinstance(event, ScheduleEvent)


def test_delete_schedule_event(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/events/{EVENT_ID}/",
        status_code=204,
    )
    client.delete_schedule_event(EVENT_ID)


def test_get_event_categories(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/categories/", json=[EVENT_CATEGORY]
    )
    categories = list(client.get_event_categories())
    assert categories == [EventCategory.from_dict(EVENT_CATEGORY, hive_client=client)]


def test_get_event_category(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/categories/{CATEGORY_ID}/",
        json=EVENT_CATEGORY,
    )
    category = client.get_event_category(CATEGORY_ID)
    assert isinstance(category, EventCategory)


def test_create_event_category(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/schedule/categories/",
        json=EVENT_CATEGORY,
    )
    category = client.create_event_category("Cat", "#fff")
    assert isinstance(category, EventCategory)


def test_update_event_category(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/schedule/categories/{CATEGORY_ID}/",
        json=EVENT_CATEGORY,
    )
    category = EventCategory.from_dict(EVENT_CATEGORY, hive_client=client)
    updated = client.update_event_category(category, name="Cat2")
    assert isinstance(updated, EventCategory)


def test_delete_event_category(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/categories/{CATEGORY_ID}/",
        status_code=204,
    )
    client.delete_event_category(CATEGORY_ID)


def test_event_attendee_crud(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/event-attendees/", json=[EVENT_ATTENDEE]
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/schedule/event-attendees/",
        json=EVENT_ATTENDEE,
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/event-attendees/{ATTENDEE_ID}/",
        status_code=204,
    )
    assert list(client.get_event_attendees()) == [
        EventAttendee.from_dict(EVENT_ATTENDEE, hive_client=client)
    ]
    assert isinstance(client.create_event_attendee(EVENT_ID, 2), EventAttendee)
    client.delete_event_attendee(ATTENDEE_ID)


def test_event_instructor_crud(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/event-instructors/", json=[EVENT_INSTRUCTOR]
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/schedule/event-instructors/",
        json=EVENT_INSTRUCTOR,
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/event-instructors/{INSTRUCTOR_LINK_ID}/",
        status_code=204,
    )
    assert list(client.get_event_instructors()) == [
        EventInstructor.from_dict(EVENT_INSTRUCTOR, hive_client=client)
    ]
    assert isinstance(client.create_event_instructor(EVENT_ID, 2), EventInstructor)
    client.delete_event_instructor(INSTRUCTOR_LINK_ID)


def test_event_tag_crud(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/event-tags/{TAG_ID}/", json=EVENT_TAG
    )
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/event-tags/", json=[EVENT_TAG]
    )
    httpx_mock.add_response(
        method="POST", url=f"{HIVE_URL}/api/core/schedule/event-tags/", json=EVENT_TAG
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{HIVE_URL}/api/core/schedule/event-tags/{TAG_ID}/",
        json=EVENT_TAG,
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/event-tags/{TAG_ID}/",
        status_code=204,
    )
    assert isinstance(client.get_event_tag(TAG_ID), EventTag)
    assert list(client.get_event_tags()) == [
        EventTag.from_dict(EVENT_TAG, hive_client=client)
    ]
    assert isinstance(client.create_event_tag("Tag", "#000"), EventTag)
    assert isinstance(client.update_event_tag(TAG_ID, name="Tag2"), EventTag)
    client.delete_event_tag(TAG_ID)


def test_event_tagging_crud(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        url=f"{HIVE_URL}/api/core/schedule/event-taggings/", json=[EVENT_TAGGING]
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{HIVE_URL}/api/core/schedule/event-taggings/",
        json=EVENT_TAGGING,
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{HIVE_URL}/api/core/schedule/event-taggings/{TAGGING_ID}/",
        status_code=204,
    )
    assert list(client.get_event_taggings()) == [
        EventTagging.from_dict(EVENT_TAGGING, hive_client=client)
    ]
    assert isinstance(client.create_event_tagging(EVENT_ID, TAG_ID), EventTagging)
    client.delete_event_tagging(TAGGING_ID)


def test_create_daily_review(httpx_mock: Any) -> None:
    client = _client(httpx_mock)
    httpx_mock.add_response(
        method="POST", url=f"{HIVE_URL}/api/core/schedule/daily_review/", json=MODULE
    )
    module = client.create_daily_review(datetime.date(2026, 1, 1))
    assert isinstance(module, Module)

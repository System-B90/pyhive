"""Tests for pyhive.locate.resolve_location (mirrored in hive-core tests/unit/locate.test.ts)."""

from __future__ import annotations

import datetime
import uuid
from types import SimpleNamespace

from pyhive.locate import RoomLocation, resolve_location

T = datetime.datetime(2026, 9, 27, 10, 0, tzinfo=datetime.timezone.utc)
ROOMS = [100, 101, 102]


def _event(
    eid: str, room: int | None, attendees: list[int], start_h: int, end_h: int
) -> SimpleNamespace:
    return SimpleNamespace(
        id=eid,
        room_id=room,
        attendees=[SimpleNamespace(id=a) for a in attendees],
        start=T.replace(hour=start_h),
        end=T.replace(hour=end_h),
    )


def test_event_room_beats_home_room() -> None:
    events = [_event("e1", 101, [7], 9, 11)]
    assert resolve_location([100, 7], ROOMS, events, T) == RoomLocation(
        101, "event", "e1"
    )


def test_falls_back_to_home_room() -> None:
    events = [_event("other", 101, [8], 9, 11), _event("ended", 102, [7], 8, 10)]
    assert resolve_location([100, 7], ROOMS, events, T) == RoomLocation(
        100, "home_room"
    )


def test_ignores_roomless_events() -> None:
    assert resolve_location(
        [100, 7], ROOMS, [_event("e", None, [7], 9, 11)], T
    ) == RoomLocation(100, "home_room")


def test_group_match_beats_room_match_then_later_start() -> None:
    events = [
        _event("by-room", 101, [100], 9, 11),
        _event("group-early", 102, [7], 8, 11),
        _event("group-late", 101, [7], 9, 11),
    ]
    assert resolve_location([100, 7], ROOMS, events, T) == RoomLocation(
        101, "event", "group-late"
    )


def test_nowhere() -> None:
    assert resolve_location([7], ROOMS, [], T) is None


def test_locate_student_live(client, program, student) -> None:  # type: ignore[no-untyped-def]
    from pyhive.locate import locate_student
    from pyhive.src.types.enums.class_type_enum import ClassTypeEnum

    suffix = uuid.uuid4().hex[:8]
    home = client.create_class(
        f"LocHome-{suffix}", program=program, users=[student], type_=ClassTypeEnum.ROOM
    )
    lab = client.create_class(
        f"LocLab-{suffix}", program=program, type_=ClassTypeEnum.ROOM
    )
    group = client.create_class(
        f"LocGroup-{suffix}",
        program=program,
        users=[student],
        type_=ClassTypeEnum.STUDENT_GROUP,
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    assert locate_student(client, student.id, now) == RoomLocation(home.id, "home_room")

    event = client.create_schedule_event(
        now - datetime.timedelta(minutes=30),
        now + datetime.timedelta(minutes=30),
        title=f"LocEvent-{suffix}",
        room=lab.id,
    )
    try:
        client.create_event_attendee(event, group.id)
        assert locate_student(client, student.id, now) == RoomLocation(
            lab.id, "event", event.id
        )
    finally:
        client.delete_schedule_event(event)

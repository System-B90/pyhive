"""
Name: locate.py
Purpose: Resolve which Hive room a student is in at a given time.
Created: 2026-09-27
Author: Michael K. Steinberg

Mirrored in hive-core ``src/locate.ts``; keep the two in sync.
See ``docs/locate-student.md`` for the rules.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from pyhive.src.types.enums.class_type_enum import ClassTypeEnum

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pyhive.client import HiveClient
    from pyhive.src.types.class_ import Class
    from pyhive.src.types.schedule_event import ScheduleEvent

# Events are fetched in a window this wide around the timestamp, because the
# API filters by containment (start__gte / end__lte), not overlap.
_WINDOW = datetime.timedelta(days=1)


@dataclass(frozen=True)
class RoomLocation:
    """Where a student is, and whether a scheduled event or their seat says so."""

    room_id: int
    source: Literal["event", "home_room"]
    event_id: object | None = None


def resolve_location(
    class_ids: Iterable[int],
    room_ids: Iterable[int],
    events: Iterable[ScheduleEvent],
    at: datetime.datetime,
) -> RoomLocation | None:
    """Pure resolver: a roomed event covering ``at`` wins, else the home room.

    :param class_ids: All classes (rooms and groups) the student sits in.
    :param room_ids: Ids of every Room-type class.
    """
    mine = set(class_ids)
    rooms = set(room_ids)
    hits = [
        (mine & {a.id for a in e.attendees}, e)
        for e in events
        if e.room_id is not None and e.start <= at < e.end
    ]
    # A student-group match is more specific than a whole-room match;
    # among equals the later start wins, like bluz's lesson activation.
    ranked = [(int(bool(m - rooms)), e.start, e) for m, e in hits if m]
    if ranked:
        event = max(ranked, key=lambda r: (r[0], r[1]))[2]
        return RoomLocation(event.room_id, "event", event.id)  # type: ignore[arg-type]
    home = sorted(mine & rooms)
    return RoomLocation(home[0], "home_room") if home else None


def locate_student(
    client: HiveClient, student_id: int, at: datetime.datetime
) -> RoomLocation | None:
    """Fetch what :func:`resolve_location` needs and resolve. Needs a Segel client."""
    student = client.get_user(student_id)
    rooms: list[Class] = list(client.get_classes(type_=ClassTypeEnum.ROOM))
    events = client.get_schedule_events(start__gte=at - _WINDOW, end__lte=at + _WINDOW)
    return resolve_location(student.class_ids or [], (c.id for c in rooms), events, at)

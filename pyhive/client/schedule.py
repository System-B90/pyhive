"""Schedule mixin for HiveClient.

Covers calendar events, event categories/tags/taggings/attendees/instructors and
the daily review generator under ``/api/core/schedule/``. Meant only for use as
a mixin on HiveClient.
"""

import datetime
from collections.abc import Iterable
from typing import TYPE_CHECKING

from ..src.types.event_category import EventCategory
from ..src.types.schedule_event import ScheduleEvent
from .client_shared import ClientCoreMixin
from .utils import UUIDLike, resolve_item_or_uuid

if TYPE_CHECKING:
    from ..src.types.event_attendee import EventAttendee
    from ..src.types.event_instructor import EventInstructor
    from ..src.types.event_tag import EventTag
    from ..src.types.event_tagging import EventTagging
    from ..src.types.lesson import Lesson
    from ..src.types.module import Module


def _optional_str(value: UUIDLike | None) -> str | None:
    return None if value is None else str(value)


class ScheduleClientMixin(ClientCoreMixin):  # pylint: disable=too-many-public-methods
    """Mixin that exposes schedule endpoints."""

    def get_schedule_events(
        self,
        *,
        start__gte: datetime.datetime | None = None,
        end__lte: datetime.datetime | None = None,
        lesson__id: "UUIDLike | Lesson | None" = None,
    ) -> Iterable[ScheduleEvent]:
        """Yield ``ScheduleEvent`` objects in the given time window."""
        return self._get_core_items(
            "/api/core/schedule/events/",
            ScheduleEvent,
            start__gte=start__gte.isoformat() if start__gte is not None else None,
            end__lte=end__lte.isoformat() if end__lte is not None else None,
            lesson__id=_optional_str(resolve_item_or_uuid(lesson__id)),
        )

    def get_schedule_event(self, event_id: "UUIDLike | ScheduleEvent") -> ScheduleEvent:
        """Return a single ``ScheduleEvent`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/schedule/events/{resolve_item_or_uuid(event_id)}/")
        assert isinstance(data, dict)
        return ScheduleEvent.from_dict(data, hive_client=self)

    def create_schedule_event(
        self,
        start: datetime.datetime,
        end: datetime.datetime,
        *,
        title: str | None = None,
        category: "UUIDLike | EventCategory | None" = None,
        room: int | None = None,
        lesson: "UUIDLike | Lesson | None" = None,
        hidden_from_students: bool = False,
        locked: bool = False,
        description: str = "",
    ) -> ScheduleEvent:
        """Create a schedule event."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "category_id": _optional_str(resolve_item_or_uuid(category)),
            "room_id": room,
            "lesson_id": _optional_str(resolve_item_or_uuid(lesson)),
            "hidden_from_students": hidden_from_students,
            "locked": locked,
            "description": description,
        }
        return ScheduleEvent.from_dict(
            self.post("/api/core/schedule/events/", payload), hive_client=self
        )

    def delete_schedule_event(self, event_id: "UUIDLike | ScheduleEvent") -> None:
        """Delete a schedule event by id."""
        self.delete(f"/api/core/schedule/events/{resolve_item_or_uuid(event_id)}/")

    # --- Categories ---

    def get_event_categories(self) -> Iterable[EventCategory]:
        """Yield all event categories."""
        return self._get_core_items("/api/core/schedule/categories/", EventCategory)

    def get_event_category(
        self, category_id: "UUIDLike | EventCategory"
    ) -> EventCategory:
        """Return a single event category by id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(
            f"/api/core/schedule/categories/{resolve_item_or_uuid(category_id)}/"
        )
        assert isinstance(data, dict)
        return EventCategory.from_dict(data, hive_client=self)

    def create_event_category(
        self,
        name: str,
        color: str,
        *,
        students_see_subject: bool = False,
        visible_to_students: bool = True,
        has_lesson: bool = False,
        hide_details_in_review: bool = False,
    ) -> EventCategory:
        """Create an event category."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            "name": name,
            "color": color,
            "students_see_subject": students_see_subject,
            "visible_to_students": visible_to_students,
            "has_lesson": has_lesson,
            "hide_details_in_review": hide_details_in_review,
        }
        return EventCategory.from_dict(
            self.post("/api/core/schedule/categories/", payload), hive_client=self
        )

    def update_event_category(
        self, category: "UUIDLike | EventCategory", **fields: object
    ) -> EventCategory:
        """Partially update an event category with the given fields."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            k: v.value if hasattr(v, "value") else v for k, v in fields.items()
        }
        data = self.patch(
            f"/api/core/schedule/categories/{resolve_item_or_uuid(category)}/", payload
        )
        assert isinstance(data, dict)
        return EventCategory.from_dict(data, hive_client=self)

    def delete_event_category(self, category_id: "UUIDLike | EventCategory") -> None:
        """Delete an event category by id."""
        self.delete(
            f"/api/core/schedule/categories/{resolve_item_or_uuid(category_id)}/"
        )

    # --- Attendees / instructors / tags / taggings ---

    def get_event_attendees(self) -> "Iterable[EventAttendee]":
        """Yield all event-attendee links."""
        from ..src.types.event_attendee import EventAttendee

        return self._get_core_items(
            "/api/core/schedule/event-attendees/", EventAttendee
        )

    def create_event_attendee(
        self, event: "UUIDLike | ScheduleEvent", attendee_class: int
    ) -> "EventAttendee":
        """Attach an attending class to an event."""
        from ..client import HiveClient
        from ..src.types.event_attendee import EventAttendee

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return EventAttendee.from_dict(
            self.post(
                "/api/core/schedule/event-attendees/",
                {
                    "event_id": str(resolve_item_or_uuid(event)),
                    "attendee_class_id": attendee_class,
                },
            ),
            hive_client=self,
        )

    def delete_event_attendee(self, attendee_id: "UUIDLike | EventAttendee") -> None:
        """Remove an event-attendee link by id."""
        self.delete(
            f"/api/core/schedule/event-attendees/{resolve_item_or_uuid(attendee_id)}/"
        )

    def get_event_instructors(self) -> "Iterable[EventInstructor]":
        """Yield all event-instructor links."""
        from ..src.types.event_instructor import EventInstructor

        return self._get_core_items(
            "/api/core/schedule/event-instructors/", EventInstructor
        )

    def create_event_instructor(
        self, event: "UUIDLike | ScheduleEvent", instructor: int
    ) -> "EventInstructor":
        """Attach an instructing user to an event."""
        from ..client import HiveClient
        from ..src.types.event_instructor import EventInstructor

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return EventInstructor.from_dict(
            self.post(
                "/api/core/schedule/event-instructors/",
                {
                    "event_id": str(resolve_item_or_uuid(event)),
                    "instructor_id": instructor,
                },
            ),
            hive_client=self,
        )

    def delete_event_instructor(
        self, instructor_link_id: "UUIDLike | EventInstructor"
    ) -> None:
        """Remove an event-instructor link by id."""
        link_id = resolve_item_or_uuid(instructor_link_id)
        self.delete(f"/api/core/schedule/event-instructors/{link_id}/")

    def get_event_tags(self) -> "Iterable[EventTag]":
        """Yield all event tags."""
        from ..src.types.event_tag import EventTag

        return self._get_core_items("/api/core/schedule/event-tags/", EventTag)

    def get_event_tag(self, tag_id: "UUIDLike | EventTag") -> "EventTag":
        """Return a single event tag by id."""
        from ..client import HiveClient
        from ..src.types.event_tag import EventTag

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(
            f"/api/core/schedule/event-tags/{resolve_item_or_uuid(tag_id)}/"
        )
        assert isinstance(data, dict)
        return EventTag.from_dict(data, hive_client=self)

    def create_event_tag(self, name: str, color: str) -> "EventTag":
        """Create an event tag."""
        from ..client import HiveClient
        from ..src.types.event_tag import EventTag

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return EventTag.from_dict(
            self.post("/api/core/schedule/event-tags/", {"name": name, "color": color}),
            hive_client=self,
        )

    def update_event_tag(
        self,
        tag_id: "UUIDLike | EventTag",
        *,
        name: str | None = None,
        color: str | None = None,
    ) -> "EventTag":
        """Partially update an event tag."""
        from ..client import HiveClient
        from ..src.types.event_tag import EventTag

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, str] = {}
        if name is not None:
            payload["name"] = name
        if color is not None:
            payload["color"] = color
        data = self.patch(
            f"/api/core/schedule/event-tags/{resolve_item_or_uuid(tag_id)}/", payload
        )
        assert isinstance(data, dict)
        return EventTag.from_dict(data, hive_client=self)

    def delete_event_tag(self, tag_id: "UUIDLike | EventTag") -> None:
        """Delete an event tag by id."""
        self.delete(f"/api/core/schedule/event-tags/{resolve_item_or_uuid(tag_id)}/")

    def get_event_taggings(self) -> "Iterable[EventTagging]":
        """Yield all event-tagging links."""
        from ..src.types.event_tagging import EventTagging

        return self._get_core_items("/api/core/schedule/event-taggings/", EventTagging)

    def create_event_tagging(
        self, event: "UUIDLike | ScheduleEvent", tag: "UUIDLike | EventTag"
    ) -> "EventTagging":
        """Attach an event tag to an event."""
        from ..client import HiveClient
        from ..src.types.event_tagging import EventTagging

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return EventTagging.from_dict(
            self.post(
                "/api/core/schedule/event-taggings/",
                {
                    "event_id": str(resolve_item_or_uuid(event)),
                    "tag_id": str(resolve_item_or_uuid(tag)),
                },
            ),
            hive_client=self,
        )

    def delete_event_tagging(self, tagging_id: "UUIDLike | EventTagging") -> None:
        """Remove an event-tagging link by id."""
        self.delete(
            f"/api/core/schedule/event-taggings/{resolve_item_or_uuid(tagging_id)}/"
        )

    # --- Daily review ---

    def create_daily_review(
        self, date: datetime.date, *, show_lesson_names: bool = True
    ) -> "Module":
        """Generate (and persist) the Daily Review module for ``date``."""
        from ..client import HiveClient
        from ..src.types.module import Module

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.post(
            "/api/core/schedule/daily_review/",
            {"date": date.isoformat(), "show_lesson_names": show_lesson_names},
        )
        assert isinstance(data, dict)
        return Module.from_dict(data, hive_client=self)

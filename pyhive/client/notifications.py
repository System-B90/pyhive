"""Notifications mixin for HiveClient.

Covers the user notification feed under ``/api/core/notification/``. Meant only
for use as a mixin on HiveClient.
"""

from collections.abc import Iterable

from ..src.types.notification import Notification
from .client_shared import ClientCoreMixin
from .utils import assert_mutually_exclusive_filters


class NotificationClientMixin(ClientCoreMixin):
    """Mixin that exposes notification endpoints."""

    def get_notifications(  # pylint: disable=too-many-arguments
        self,
        *,
        assignment: int | None = None,
        assignment__exercise: int | None = None,
        assignment__exercise__in: list[int] | None = None,
        from_user__isnull: bool | None = None,
        help: int | None = None,  # pylint: disable=redefined-builtin
        help__in: list[int] | None = None,
        was_read: bool | None = None,
    ) -> Iterable[Notification]:
        """Yield ``Notification`` objects filtered by the provided criteria."""
        assert_mutually_exclusive_filters(
            assignment__exercise, assignment__exercise__in
        )
        assert_mutually_exclusive_filters(help, help__in)
        return self._get_core_items(
            "/api/core/notification/",
            Notification,
            assignment=assignment,
            assignment__exercise=assignment__exercise,
            assignment__exercise__in=assignment__exercise__in,
            from_user__isnull=from_user__isnull,
            help=help,
            help__in=help__in,
            was_read=was_read,
        )

    def get_notification(self, notification_id: int) -> Notification:
        """Return a single ``Notification`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/notification/{notification_id}/")
        assert isinstance(data, dict)
        return Notification.from_dict(data, hive_client=self)

    def create_notification(
        self,
        user: int,
        *,
        help: int | None = None,  # pylint: disable=redefined-builtin
        assignment: int | None = None,
        comment: str = "",
        was_read: bool = False,
    ) -> Notification:
        """Create a notification for ``user``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            "user": user,
            "help": help,
            "assignment": assignment,
            "comment": comment,
            "was_read": was_read,
        }
        return Notification.from_dict(
            self.post("/api/core/notification/", payload), hive_client=self
        )

    def update_notification(
        self, notification: Notification, *, was_read: bool | None = None
    ) -> Notification:
        """Mark a notification read/unread (or pass no flag to re-save)."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {}
        if was_read is not None:
            payload["was_read"] = was_read
        data = self.patch(f"/api/core/notification/{notification.id}/", payload)
        assert isinstance(data, dict)
        return Notification.from_dict(data, hive_client=self)

    def delete_notification(self, notification_id: int) -> None:
        """Delete a notification by id."""
        self.delete(f"/api/core/notification/{notification_id}/")

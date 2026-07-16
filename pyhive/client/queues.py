"""Queues mixin for HiveClient.

Provides retrieval of queue records.
"""

from typing import TYPE_CHECKING, Optional

from pyhive.client.utils import resolve_item_or_id

from ..src.types.queue import Queue
from .client_shared import ClientCoreMixin

if TYPE_CHECKING:
    from ..src.types.module import ModuleLike
    from ..src.types.user import UserLike
    from ..src.types.queue import QueueLike


class QueuesClientMixin(ClientCoreMixin):
    """Mixin that exposes queue retrieval endpoints."""

    def get_queue(self, queue_id: int) -> Queue:
        """Return a single queue by ``queue_id``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/queues/{queue_id}/")
        assert isinstance(data, dict)
        return Queue.from_dict(
            data,
            hive_client=self,
        )

    def create_queue(
        self,
        name: str,
        description: str = "",
        module: Optional["ModuleLike"] = None,
        user: Optional["UserLike"] = None,
    ) -> Queue:
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"

        payload: dict[str, str | int | None] = {
            "name": name,
            "description": description,
            "module": None,
            "user": None,
        }

        if module is not None:
            payload["module"] = resolve_item_or_id(module)
        if user is not None:
            payload["user"] = resolve_item_or_id(user)

        return Queue.from_dict(
            self.post("/api/core/queues/", payload),
            hive_client=self,
        )

    def delete_queue(self, queue: "QueueLike") -> None:
        self.delete(f"/api/core/queues/{resolve_item_or_id(queue)}/")

"""Seating mixin for HiveClient.

Covers classroom seating under ``/api/core/management/seating/``. Meant only
for use as a mixin on HiveClient.
"""

from collections.abc import Iterable

from ..src.types.seating import Seating
from .client_shared import ClientCoreMixin
from .utils import resolve_item_or_id


class SeatingClientMixin(ClientCoreMixin):
    """Mixin that exposes seating endpoints."""

    def get_seatings(
        self,
        *,
        classroom__id: int | None = None,
    ) -> Iterable[Seating]:
        """Yield ``Seating`` objects, optionally filtered by classroom."""
        return self._get_core_items(
            "/api/core/management/seating/",
            Seating,
            classroom__id=classroom__id,
        )

    def get_seating(self, seating_id: int) -> Seating:
        """Return a single ``Seating`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/management/seating/{seating_id}/")
        assert isinstance(data, dict)
        return Seating.from_dict(data, hive_client=self)

    def create_seating(
        self,
        classroom: int,
        x: int,
        y: int,
        *,
        hostname: str | None = None,
        hanich: int | None = None,
    ) -> Seating:
        """Create a seat in ``classroom`` at grid position ``(x, y)``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            "classroom": resolve_item_or_id(classroom),
            "x": x,
            "y": y,
            "hostname": hostname,
            "hanich": hanich,
        }
        return Seating.from_dict(
            self.post("/api/core/management/seating/", payload), hive_client=self
        )

    def update_seating(self, seating: Seating, **fields: object) -> Seating:
        """Partially update a seat with the given fields (x/y/classroom/hanich/hostname)."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.patch(f"/api/core/management/seating/{seating.id}/", dict(fields))
        assert isinstance(data, dict)
        return Seating.from_dict(data, hive_client=self)

    def delete_seating(self, seating_id: int) -> None:
        """Delete a seat by id."""
        self.delete(f"/api/core/management/seating/{seating_id}/")

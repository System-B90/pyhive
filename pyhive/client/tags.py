"""Tags mixin for HiveClient.

Covers exercise tags under ``/api/core/tags/``. Meant only for use as a mixin
on HiveClient.
"""

from collections.abc import Iterable

from ..src.types.tag import Tag
from .client_shared import ClientCoreMixin


class TagClientMixin(ClientCoreMixin):
    """Mixin that exposes tag endpoints."""

    def get_tags(self) -> Iterable[Tag]:
        """Yield all tags."""
        return self._get_core_items("/api/core/tags/", Tag)

    def get_tag(self, tag_id: int) -> Tag:
        """Return a single ``Tag`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/tags/{tag_id}/")
        assert isinstance(data, dict)
        return Tag.from_dict(data, hive_client=self)

    def create_tag(self, name: str, color: str) -> Tag:
        """Create a tag."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        return Tag.from_dict(
            self.post("/api/core/tags/", {"name": name, "color": color}),
            hive_client=self,
        )

    def update_tag(
        self, tag: Tag, *, name: str | None = None, color: str | None = None
    ) -> Tag:
        """Partially update a tag."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, str] = {}
        if name is not None:
            payload["name"] = name
        if color is not None:
            payload["color"] = color
        data = self.patch(f"/api/core/tags/{tag.id}/", payload)
        assert isinstance(data, dict)
        return Tag.from_dict(data, hive_client=self)

    def delete_tag(self, tag_id: int) -> None:
        """Delete a tag by id."""
        self.delete(f"/api/core/tags/{tag_id}/")

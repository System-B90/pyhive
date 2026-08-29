"""System mixin for HiveClient.

Covers server time and the PowerSync token endpoint. Meant only for use as a
mixin on HiveClient.
"""

from ..src.types.powersync_token import PowerSyncToken
from .client_shared import ClientCoreMixin


class SystemClientMixin(ClientCoreMixin):
    """Mixin that exposes system-level endpoints."""

    def get_server_time(self) -> str:
        """Return the server's current time string."""
        data = self._get("/api/core/time/").json()
        assert isinstance(data, str)
        return data

    def get_powersync_token(self) -> PowerSyncToken:
        """Return a fresh PowerSync sync token."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get("/api/core/powersync/token/")
        assert isinstance(data, dict)
        return PowerSyncToken.from_dict(data, hive_client=self)

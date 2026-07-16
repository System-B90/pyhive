"""Version mixin for HiveClient.

Provides access to the Hive server version information.
"""

import re

from .client_shared import ClientCoreMixin


class VersionClientMixin(ClientCoreMixin):
    """Mixin that exposes the server-version endpoint."""

    def get_hive_version(self) -> str:
        """Return the Hive server version string (e.g., '1.2.3')."""
        data = self.get("/api/core/schema/")
        assert isinstance(data, dict)
        version = data.get("info", {}).get("version", "")
        if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+", version):
            raise ValueError("Invalid version string received from server")
        return version

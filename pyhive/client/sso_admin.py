"""SSO admin mixin for HiveClient.

Covers SSO application management under ``/api/core/sso/``. Meant only for use
as a mixin on HiveClient.
"""

from collections.abc import Iterable

import httpx

from ..src.types.client_info import ClientInfo
from ..src.types.sso_application import SsoApplication
from .client_shared import ClientCoreMixin


class SsoAdminClientMixin(ClientCoreMixin):
    """Mixin that exposes SSO application endpoints."""

    def get_sso_applications(self) -> Iterable[SsoApplication]:
        """Yield all registered SSO applications."""
        return self._get_core_items("/api/core/sso/applications/", SsoApplication)

    def get_sso_application(self, application_id: int) -> SsoApplication:
        """Return a single ``SsoApplication`` by its id."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(f"/api/core/sso/applications/{application_id}/")
        assert isinstance(data, dict)
        return SsoApplication.from_dict(data, hive_client=self)

    def create_sso_application(
        self,
        name: str,
        *,
        redirect_uris: str = "",
        skip_authorization: bool = False,
    ) -> SsoApplication:
        """Register an SSO application (client id/secret are assigned by the server)."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        payload: dict[str, object] = {
            "name": name,
            "redirect_uris": redirect_uris,
            "skip_authorization": skip_authorization,
        }
        return SsoApplication.from_dict(
            self.post("/api/core/sso/applications/", payload), hive_client=self
        )

    def update_sso_application(
        self, application: SsoApplication, **fields: object
    ) -> SsoApplication:
        """Partially update an SSO application with the given fields."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.patch(f"/api/core/sso/applications/{application.id}/", dict(fields))
        assert isinstance(data, dict)
        return SsoApplication.from_dict(data, hive_client=self)

    def delete_sso_application(self, application_id: int) -> None:
        """Delete an SSO application by id."""
        self.delete(f"/api/core/sso/applications/{application_id}/")

    def get_client_info(self, client_id: str) -> ClientInfo:
        """Return public metadata for the SSO client ``client_id``."""
        from ..client import HiveClient

        assert isinstance(self, HiveClient), "self must be an instance of HiveClient"
        data = self.get(
            "/api/core/sso/client-info/",
            params=httpx.QueryParams({"client_id": client_id}),
        )
        assert isinstance(data, dict)
        return ClientInfo.from_dict(data, hive_client=self)

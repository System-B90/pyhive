"""
Name: sso_application.py
Purpose: Model for registered SSO/OIDC applications in Hive.
Created: 2026-08-23
Author: Michael K. Steinberg
"""

from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from typing_extensions import Self

from pydantic import Field

from .core_item import HiveCoreItem

if TYPE_CHECKING:
    from ...client import HiveClient


class SsoApplication(HiveCoreItem):
    """A registered SSO application (client id/secret, redirect URIs, owner)."""

    hive_client: Annotated["HiveClient", Field(exclude=True, repr=False)]
    id: int
    name: str
    redirect_uris: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    owner: int | None = None
    skip_authorization: bool = False

    @classmethod
    def from_dict(cls, src_dict: dict[str, Any], hive_client: "HiveClient") -> Self:
        data = dict(src_dict)
        data["hive_client"] = hive_client
        return cls.model_validate(data)


T = TypeVar("T", bound="SsoApplication")

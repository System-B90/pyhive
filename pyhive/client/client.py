"""High-level Hive API client aggregator."""

from types import TracebackType
from typing import TYPE_CHECKING, List, Literal, Optional, Union

from pyhive.client.sso_utils import generate_sso_client_credentials, get_sso_token

from ..src.api_versions import (
    LATEST_API_VERSION,
    MIN_API_VERSION,
    SUPPORTED_API_VERSIONS,
)
from .assignment_responses import AssignmentResponsesClientMixin
from .assignments import AssignmentClientMixin
from .classes import ClassesClientMixin
from .exercises import ExerciseClientMixin
from .fields import FieldsClientMixin
from .help import HelpClientMixin
from .modules import ModuleClientMixin
from .programs import ProgramClientMixin
from .queues import QueuesClientMixin
from .subjects import SubjectClientMixin
from .users import UserClientMixin
from .version import VersionClientMixin

if TYPE_CHECKING:
    from httpx import Timeout
    from httpx._types import ProxyTypes


class HiveClient(  # pylint: disable=too-many-ancestors,abstract-method
    ProgramClientMixin,
    SubjectClientMixin,
    ModuleClientMixin,
    ExerciseClientMixin,
    AssignmentClientMixin,
    UserClientMixin,
    ClassesClientMixin,
    FieldsClientMixin,
    AssignmentResponsesClientMixin,
    QueuesClientMixin,
    HelpClientMixin,
    VersionClientMixin,
):
    """Aggregated HTTP client for accessing Hive API resources."""

    def __init__(
        self,
        username: str,
        password: str,
        hive_url: str,
        *,
        skip_version_check: bool = False,
        timeout: Optional[Union["Timeout", float]] = None,
        headers: Optional[dict[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
        proxy: Optional["ProxyTypes"] = None,
        existing_token: str | None = None,
        auth_strategy: Literal["sso", "cache"] | None = None,
        refresh_token: Optional[str] = None,
        **kwargs: object,
    ):
        super().__init__(
            username,
            password,
            hive_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
            proxy=proxy,
            existing_token=existing_token,
            auth_strategy=auth_strategy,
            refresh_token=refresh_token,
            **kwargs,
        )
        if not skip_version_check:
            self._api_version_check()

    @classmethod
    def from_api_token(
        cls,
        api_token: str,
        hive_url: str,
        *,
        refresh_token: Optional[str] = None,
        timeout: Optional[Union["Timeout", float]] = None,
        headers: Optional[dict[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
        proxy: Optional["ProxyTypes"] = None,
        skip_version_check: bool = False,
        auth_strategy: Literal["sso", "cache"] | None = None,
        **kwargs: object,
    ) -> "HiveClient":
        """Construct a client using an existing Hive API token.

        This is mainly intended for advanced integrations. In most user-facing
        scenarios, prefer :meth:`from_sso`, which performs the browser-based
        Hive SSO flow and then creates the client from the resulting token.

        Automatic token refresh is *not* supported in this mode: if the token
        expires, create a new :class:`HiveClient` with a freshly-issued token.
        """

        return cls(
            "token-auth",  # placeholder username for repr/debugging
            "unused",
            hive_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
            proxy=proxy,
            skip_version_check=skip_version_check,
            existing_token=api_token,
            refresh_token=refresh_token,
            auth_strategy=auth_strategy,
            **kwargs,
        )

    @classmethod
    def from_sso(
        cls,
        hive_url: str,
        *,
        timeout: Optional[Union["Timeout", float]] = None,
        headers: Optional[dict[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
        proxy: Optional["ProxyTypes"] = None,
        skip_version_check: bool = False,
        **kwargs: object,
    ) -> "HiveClient":
        """
        Instantiate a HiveClient using interactive browser-based SSO authentication.

        Args:
            hive_url (str): The base URL of the Hive server.
            timeout (Optional[Union[Timeout, float]]): Request timeout configuration.
            headers (Optional[dict[str, str]]): Additional headers to apply to the client.
            verify (Optional[Union[bool, str]]): SSL verification requirements.
            proxy (Optional[ProxyTypes]): Proxy configuration.
            skip_version_check (bool): Bypass API version compatibility checking.
            **kwargs (object): Additional client configuration parameters.

        Returns:
            HiveClient: An authenticated instance of the HiveClient.
        """

        # Trigger the browser-based OIDC flow
        user_token = get_sso_token(hive_url=hive_url, verify=verify)

        # Delegate to from_api_token to construct the actual client
        return cls.from_api_token(
            api_token=user_token[0],
            refresh_token=user_token[1],
            hive_url=hive_url,
            timeout=timeout,
            headers=headers,
            verify=verify,
            proxy=proxy,
            skip_version_check=skip_version_check,
            auth_strategy="sso",
            **kwargs,
        )

    def __repr__(self) -> str:
        """Return a short representation including username and hive_url.

        The representation intentionally omits secrets.
        """

        return f"HiveClient({self.username!r}, input(), {self.hive_url!r})"

    def __enter__(self) -> "HiveClient":
        """Enter context manager and return this client instance.

        The underlying :class:`httpx.Client` is managed by this object's
        lifecycle; entering the context returns the authenticated client so
        callers can perform API calls.
        """
        return self

    def __exit__(
        self,
        type_: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the context and close the underlying httpx session.

        This delegates to the managed :class:`httpx.Client`'s ``__exit__``
        method to ensure resources are released.
        """

        self._session.__exit__(type_, value, traceback)

    def _api_version_check(self) -> None:
        """Validate that the Hive server API version is supported.

        Fetches the server version via ``get_hive_version`` and verifies it is present
        in ``SUPPORTED_API_VERSIONS``. If unsupported, raises a RuntimeError with
        guidance to align the client and server versions.

        Raises:
            RuntimeError: If the server API version is not supported by this client.
        """
        version_str = self.get_hive_version()
        if version_str not in SUPPORTED_API_VERSIONS:
            supported_range = f"{MIN_API_VERSION} .. {LATEST_API_VERSION}"
            raise RuntimeError(
                (
                    f"Unsupported Hive API version '{version_str}'. Supported versions: {supported_range}. "
                    f"Please upgrade/downgrade the server or use a compatible client."
                )
            )

    def register_sso_service(
        self,
        service_name: str,
        redirect_uris: Optional[List[str] | str] = None,
    ) -> dict[str, str]:
        return generate_sso_client_credentials(self, service_name, redirect_uris)

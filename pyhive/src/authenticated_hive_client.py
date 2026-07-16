"""Authentication helpers and a small authenticated HTTP client for Hive.

This module provides decorators that add retry and token-refresh behavior to
HTTP calls and an internal ``_AuthenticatedHiveClient`` which wraps an
:class:`httpx.Client` and handles login/refresh for the Hive API.
"""

import functools
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeVar, cast

import httpx
from httpx import HTTPStatusError

if TYPE_CHECKING:
    from httpx._types import ProxyTypes

F = TypeVar("F", bound=Callable[..., httpx.Response])

MAX_RETRIES_ON_SERVER_ERRORS = 5
INITIAL_BACKOFF_SECONDS = 0.5


def _retry_on_bad_gateway(func: F) -> F:
    """Decorator: retry a request when the server returns HTTP 502.

    The wrapped function is expected to return an :class:`httpx.Response`.
    Retries use exponential backoff and will re-raise the final response's
    HTTP error if all retries fail.
    """

    @functools.wraps(func)
    def wrapper(
        self: "AuthenticatedHiveClient", *args: Any, **kwargs: Any
    ) -> httpx.Response:
        delay = INITIAL_BACKOFF_SECONDS
        if MAX_RETRIES_ON_SERVER_ERRORS <= 0:
            raise ValueError("MAX_RETRIES_ON_SERVER_ERRORS must be greater than 0")
        response = None
        for attempt in range(MAX_RETRIES_ON_SERVER_ERRORS):
            response = func(self, *args, **kwargs)
            if response.status_code != httpx.codes.BAD_GATEWAY.value:
                return response
            if attempt < MAX_RETRIES_ON_SERVER_ERRORS - 1:
                time.sleep(delay)
                delay *= 2
        assert response is not None
        response.raise_for_status()
        return response

    return cast("F", wrapper)


def _refresh_token_on_unauthorized(func: F) -> F:
    """Decorator: refresh access token and retry on HTTP 401 Unauthorized.

    If the wrapped function returns a 401 status, the client's
    ``_refresh_access_token`` is called and the request is retried once.
    """

    @functools.wraps(func)
    def wrapper(
        self: "AuthenticatedHiveClient", *args: Any, **kwargs: Any
    ) -> httpx.Response:
        response = func(self, *args, **kwargs)
        if response.status_code == httpx.codes.UNAUTHORIZED.value:
            self._refresh_access_token()  # pylint: disable=protected-access
            response = func(self, *args, **kwargs)
        if response.status_code == httpx.codes.BAD_REQUEST.value:
            raise HTTPStatusError(
                f"Bad request! {response.json()}",
                request=response.request,
                response=response,
            )
        response.raise_for_status()
        return response

    return cast("F", wrapper)


def _with_retries_and_token_refresh(func: F) -> F:
    """Compose the retry and token-refresh decorators.

    Use this to wrap HTTP methods so they automatically handle transient
    502 errors and expired access tokens.
    """

    return _refresh_token_on_unauthorized(_retry_on_bad_gateway(func))


class AuthenticatedHiveClient:
    """Internal class used to handle authentication and re-authentication with Hive web endpoint."""

    _refresh_token: str
    _access_token: str
    _session: httpx.Client
    username: str
    _auth_strategy: Literal["password", "sso", "token_only", "cache"]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        username: str,
        password: str,
        hive_url: str,
        *,
        timeout: httpx.Timeout | float | None = None,
        headers: dict[str, str] | None = None,
        verify: bool | str | None = None,
        proxy: Optional["ProxyTypes"],
        existing_token: str | None = None,
        auth_strategy: Literal["sso", "cache"] | None = None,
        refresh_token: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Create an authenticated client.

        Common HTTP client options may be provided explicitly (typed) or via
        ``**kwargs`` and will be forwarded to :class:`httpx.Client`.

        Typed kwargs provided (timeout, headers, verify) take precedence; the
        rest are forwarded from ``kwargs``.
        """
        self.username = username
        self.hive_url = hive_url

        client_kwargs: dict[str, Any] = {}
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        if headers is not None:
            client_kwargs["headers"] = headers
        if verify is not None:
            client_kwargs["verify"] = verify
        if proxy is not None:
            client_kwargs["proxy"] = proxy

        # Include any other httpx.Client kwargs passed in **kwargs
        client_kwargs.update(kwargs)

        self._session = httpx.Client(
            base_url=hive_url,
            **client_kwargs,
        ).__enter__()

        # Decide how to authenticate: either via username/password (default)
        # or by using an already-issued API token.
        if existing_token is not None:
            self._access_token = existing_token
            self._session.headers.update(
                {"Authorization": f"Bearer {self._access_token}"}
            )
            if auth_strategy in ("sso", "cache"):
                assert refresh_token is not None, (
                    "Using SSO but no refresh token was given!"
                )
                self._auth_strategy = auth_strategy
                self._refresh_token = refresh_token
            else:
                # Use the provided token directly; no login or refresh endpoint.
                self._auth_strategy = "token_only"
                # No refresh token is available in this mode.
                self._refresh_token = ""
        else:
            self._auth_strategy = "password"
            self._login(username, password)

    def _login(self, username: str, password: str) -> None:
        """Perform an authentication request and store access/refresh tokens.

        This sets the ``Authorization`` header on the underlying session.
        """

        response = self._session.post(
            "/api/core/token/",
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access"]
        self._refresh_token = data["refresh"]

        self._session.headers.update({"Authorization": f"Bearer {self._access_token}"})

    def _refresh_access_token(self) -> None:
        """Refresh the access token using the stored refresh token.

        Updates the stored access and refresh tokens and the session header.

        In ``password`` mode this calls the Hive API token refresh endpoint.
        In ``token_only`` mode (when an existing token was supplied at
        construction time) automatic refresh is not supported and a
        ``RuntimeError`` is raised so callers can obtain a fresh token from
        their SSO/web flow and recreate the client.
        """

        if self._auth_strategy == "token_only":
            msg = (
                "Cannot refresh access token when using an existing API token. "
                "Please acquire a new token from your SSO/web authentication "
                "flow and create a new HiveClient instance."
            )
            raise RuntimeError(msg)

        response = self._session.post(
            "/api/core/token/refresh/",
            json={"refresh": self._refresh_token},
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access"]
        self._refresh_token = data["refresh"]

        self._session.headers.update({"Authorization": f"Bearer {self._access_token}"})

    @_with_retries_and_token_refresh
    def _get(
        self,
        endpoint: str,
        params: httpx.QueryParams | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response:
        """Low-level GET that returns an :class:`httpx.Response`.

        This is decorated to handle retries and token refresh automatically.
        """

        return self._session.get(
            endpoint,
            params=params,
            headers={"Accept": "application/json"},
            follow_redirects=follow_redirects,
        )

    @_with_retries_and_token_refresh
    def _post(self, endpoint: str, data: dict[Any, Any]) -> httpx.Response:
        """Low-level POST that returns an :class:`httpx.Response` with JSON body.

        The ``data`` is JSON-encoded into the request body.
        """

        return self._session.post(endpoint, json=data)

    @_with_retries_and_token_refresh
    def _patch(self, endpoint: str, data: dict[Any, Any]) -> httpx.Response:
        """Low-level PATCH request; returns :class:`httpx.Response`.

        The ``data`` is JSON-encoded into the request body.
        """

        return self._session.patch(endpoint, json=data)

    @_with_retries_and_token_refresh
    def _delete(self, endpoint: str) -> httpx.Response:
        """Low-level DELETE request; returns :class:`httpx.Response`."""

        return self._session.delete(endpoint)

    @_with_retries_and_token_refresh
    def _put(self, endpoint: str, data: dict[Any, Any]) -> httpx.Response:
        """Low-level PUT request; returns :class:`httpx.Response`.

        The ``data`` is JSON-encoded into the request body.
        """

        return self._session.put(endpoint, json=data)

    def get(
        self,
        endpoint: str,
        params: httpx.QueryParams | None = None,
        follow_redirects: bool = False,
    ) -> dict[str, Any] | list[Any]:
        """High-level GET that returns parsed JSON from the response.

        This calls the decorated ``_get`` helper and returns its JSON body.
        """

        response = self._get(endpoint, params, follow_redirects=follow_redirects).json()
        if not isinstance(response, (dict, list)):
            raise TypeError("Expected JSON object or list from GET response")
        return response

    def post(self, endpoint: str, data: dict[Any, Any]) -> dict[str, Any]:
        """High-level POST that returns parsed JSON from the response.

        The ``data`` dict is JSON-encoded for the request body.

        Raises an exception with response JSON included for HTTP 400.
        """
        try:
            resp = self._post(endpoint, data)
            resp.raise_for_status()
        except HTTPStatusError as exc:
            # If status code is 400, raise with response JSON
            if exc.response.status_code == 400:
                try:
                    error_json = exc.response.json()
                except Exception:  # pylint: disable=broad-except
                    error_json = exc.response.text
                raise ValueError(f"HTTP 400 Error: {error_json}") from exc
            # Otherwise, re-raise the original HTTP error
            raise
        data = resp.json()
        if not isinstance(data, dict):
            raise TypeError("Expected JSON object from POST response")
        return data

    def delete(self, endpoint: str, force: bool = False) -> None:  # pylint: disable=unused-argument
        response = self._delete(endpoint)
        if response.status_code != httpx.codes.NO_CONTENT.value:  # 204 No response body
            raise RuntimeError("Failed to delete!")

    def put(self, endpoint: str, data: dict[Any, Any]) -> dict[Any, Any]:
        data = self._put(endpoint, data).json()
        if not isinstance(data, dict):
            raise TypeError("Expected JSON object from PUT response")
        return data

    def __repr__(self) -> str:
        """Return a short representation including username and hive_url.

        The representation intentionally omits secrets.
        """

        return f"HiveClient({self.username!r}, '***', {self.hive_url!r})"

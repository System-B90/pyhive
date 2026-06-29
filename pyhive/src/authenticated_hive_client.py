"""Authentication helpers and a small authenticated HTTP client for Hive.

This module provides decorators that add retry and token-refresh behavior to
HTTP calls and an internal ``_AuthenticatedHiveClient`` which wraps an
:class:`httpx.Client` and handles login/refresh for the Hive API.
"""

import functools
import time
from collections.abc import Callable
from types import TracebackType
from typing import Any, TypeVar, cast

import httpx

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
    def wrapper(self: "_AuthenticatedHiveClient", *args: Any, **kwargs: Any):
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
    def wrapper(self: "_AuthenticatedHiveClient", *args: Any, **kwargs: Any):
        response = func(self, *args, **kwargs)
        if response.status_code == httpx.codes.UNAUTHORIZED.value:
            self._refresh_access_token()  # pylint: disable=protected-access
            response = func(self, *args, **kwargs)
        response.raise_for_status()
        return response

    return cast("F", wrapper)


def _with_retries_and_token_refresh(func: F) -> F:
    """Compose the retry and token-refresh decorators.

    Use this to wrap HTTP methods so they automatically handle transient
    502 errors and expired access tokens.
    """

    return _refresh_token_on_unauthorized(_retry_on_bad_gateway(func))


class _AuthenticatedHiveClient:
    """Internal class used to handle authentication and re-authentication with Hive web endpoint."""

    _refresh_token: str
    _access_token: str
    _session: httpx.Client
    username: str

    def __init__(  # pylint: disable=too-many-arguments
        self,
        username: str,
        password: str,
        hive_url: str,
        *,
        timeout: httpx.Timeout | float | None = None,
        headers: dict[str, str] | None = None,
        verify: bool | str | None = None,
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

        # Include any other httpx.Client kwargs passed in **kwargs
        client_kwargs.update(kwargs)

        self._session = httpx.Client(
            base_url=hive_url,
            **client_kwargs,
        ).__enter__()
        self._login(username, password)

    def __enter__(self) -> "_AuthenticatedHiveClient":
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
    ) -> bool | None:
        """Exit the context and close the underlying httpx session.

        This delegates to the managed :class:`httpx.Client`'s ``__exit__``
        method to ensure resources are released.
        """

        self._session.__exit__(type_, value, traceback)

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
        """

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
        self, endpoint: str, params: httpx.QueryParams | None = None
    ) -> httpx.Response:
        """Low-level GET that returns an :class:`httpx.Response`.

        This is decorated to handle retries and token refresh automatically.
        """

        return self._session.get(endpoint, params=params)

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

    def get(self, endpoint: str, params: httpx.QueryParams | None = None) -> Any:
        """High-level GET that returns parsed JSON from the response.

        This calls the decorated ``_get`` helper and returns its JSON body.
        """

        return self._get(endpoint, params).json()

    def post(self, endpoint: str, data: dict[Any, Any]) -> Any:
        """High-level POST that returns parsed JSON from the response.

        The ``data`` dict is JSON-encoded for the request body.
        """

        return self._post(endpoint, data).json()

    def __repr__(self) -> str:
        """Return a short representation including username and hive_url.

        The representation intentionally omits secrets.
        """

        return f"HiveClient({self.username!r}, '***', {self.hive_url!r})"

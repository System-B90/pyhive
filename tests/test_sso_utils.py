"""
Name: test_sso_utils.py
Purpose: Unit tests for the OIDC SSO authentication utilities in the PyHive client.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import base64
import hashlib
import socket
import threading
import time
from unittest import mock
import urllib.request
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from pyhive.client import sso_utils


def get_free_port() -> int:
    """
    Acquire a dynamically assigned free ephemeral port from the OS.

    Args:
        None

    Returns:
        int: A free port number.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture
def dynamic_port(monkeypatch: pytest.MonkeyPatch) -> int:
    """
    Pytest fixture to patch LOCAL_SERVER_PORT with a free port to prevent
    'Address already in use' collisions across concurrent or sequential tests.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatching fixture.

    Returns:
        int: The dynamically assigned port number used for the test.
    """
    port = get_free_port()
    monkeypatch.setattr(sso_utils, "LOCAL_SERVER_PORT", port)
    return port


@pytest.fixture
def mock_httpx_post() -> Generator[MagicMock, None, None]:
    """
    Pytest fixture to mock the httpx.Client.post method.

    Args:
        None

    Returns:
        Generator[MagicMock, None, None]: Yields the mocked post method.
    """
    with patch("httpx.Client.post") as mock_post:
        yield mock_post


def trigger_callback(port: int, query_string: str) -> None:
    """
    Background worker to simulate the OIDC provider redirecting the user's browser
    back to the local Flask server.

    Args:
        port (int): The port the local Flask server is running on.
        query_string (str): The GET parameters to append to the callback URL.

    Returns:
        None
    """
    time.sleep(0.5)  # Allow Flask server thread time to initialize
    url = f"http://localhost:{port}/callback?{query_string}"
    try:
        urllib.request.urlopen(url)
    except Exception:
        # Ignore HTTP errors (like 400 Bad Request) raised intentionally by the callback logic
        pass


def test_generate_pkce_pair() -> None:
    """
    Test that the PKCE generator produces a valid verifier and S256 challenge.

    Args:
        None

    Returns:
        None
    """
    verifier, challenge = sso_utils._generate_pkce_pair()  # pyright: ignore[reportPrivateUsage]

    assert isinstance(verifier, str)
    assert len(verifier) >= 43  # RFC 7636 requirement
    assert isinstance(challenge, str)

    # Re-verify the S256 hashing manually
    expected_hash = hashlib.sha256(verifier.encode("ascii")).digest()
    expected_challenge = (
        base64.urlsafe_b64encode(expected_hash).decode("ascii").rstrip("=")
    )

    assert challenge == expected_challenge


def test_start_local_callback_server_success(
    dynamic_port: int, mock_httpx_post: MagicMock
) -> None:
    """
    Test the successful completion of the local callback server and token exchange.

    Args:
        dynamic_port (int): Injected free port for the Flask server.
        mock_httpx_post (MagicMock): Mocked httpx POST method.

    Returns:
        None
    """
    # Setup the mock response for the token exchange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "mock_hive_token_123"}
    mock_httpx_post.return_value = mock_response

    # Fire the background browser simulation
    threading.Thread(
        target=trigger_callback, args=(dynamic_port, "code=mock_auth_code_456")
    ).start()

    # Execute the method under test
    token = sso_utils._start_local_callback_server(  # pyright: ignore[reportPrivateUsage]
        hive_url="https://mock-hive.org",
        client_id="test_client",
        client_secret="test_secret",
        code_verifier="test_verifier",
    )

    assert token == "mock_hive_token_123"
    mock_httpx_post.assert_called_once()

    # Verify the POST payload
    call_kwargs = mock_httpx_post.call_args.kwargs
    assert call_kwargs["data"]["code"] == "mock_auth_code_456"
    assert call_kwargs["data"]["grant_type"] == "authorization_code"


def test_start_local_callback_server_auth_error(dynamic_port: int) -> None:
    """
    Test that OIDC provider errors passed to the callback raise a PermissionError.

    Args:
        dynamic_port (int): Injected free port for the Flask server.

    Returns:
        None
    """
    # Fire the background browser simulation with an error
    query = "error=invalid_request&error_description=Code+challenge+required"
    threading.Thread(target=trigger_callback, args=(dynamic_port, query)).start()

    with pytest.raises(PermissionError) as exc_info:
        sso_utils._start_local_callback_server(  # pyright: ignore[reportPrivateUsage]
            hive_url="https://mock-hive.org",
            client_id="test_client",
            client_secret="test_secret",
            code_verifier="test_verifier",
        )

    assert "invalid_request" in str(exc_info.value)
    assert "Code challenge required" in str(exc_info.value)


def test_start_local_callback_server_exchange_failure(
    dynamic_port: int, mock_httpx_post: MagicMock
) -> None:
    """
    Test that a failed HTTP POST during token exchange raises a RuntimeError.

    Args:
        dynamic_port (int): Injected free port for the Flask server.
        mock_httpx_post (MagicMock): Mocked httpx POST method.

    Returns:
        None
    """
    # Setup the mock response for a failed token exchange
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized client"
    mock_httpx_post.return_value = mock_response

    threading.Thread(
        target=trigger_callback, args=(dynamic_port, "code=mock_auth_code")
    ).start()

    with pytest.raises(RuntimeError) as exc_info:
        sso_utils._start_local_callback_server(  # pyright: ignore[reportPrivateUsage]
            hive_url="https://mock-hive.org",
            client_id="test_client",
            client_secret="test_secret",
            code_verifier="test_verifier",
        )

    assert "Token exchange failed (HTTP 401)" in str(exc_info.value)


@patch("pyhive.client.sso_utils.webbrowser.open")
@patch("pyhive.client.sso_utils._start_local_callback_server")
def test_get_sso_token(
    mock_start_server: MagicMock, mock_webbrowser: MagicMock
) -> None:
    """
    Test that get_sso_token builds the correct URL and delegates to the callback server.

    Args:
        mock_start_server (MagicMock): Mocked internal server starter.
        mock_webbrowser (MagicMock): Mocked webbrowser module.

    Returns:
        None
    """
    mock_start_server.return_value = "final_access_token"
    hive_url = "https://mock-hive.org"

    token = sso_utils.get_sso_token(hive_url=hive_url, verify=False)

    assert token == "final_access_token"

    # Verify the browser was instructed to open
    mock_webbrowser.assert_called_once()
    opened_url = mock_webbrowser.call_args[0][0]

    assert opened_url.startswith(f"{hive_url}/sso/authorize")
    assert "response_type=code" in opened_url
    assert "code_challenge_method=S256" in opened_url

    # Verify the server starter was called with the correct pass-through arguments
    mock_start_server.assert_called_once_with(
        hive_url=hive_url,
        client_id="642uP9TG10CQYtDBV3SIGjEN6fhQDsZMWM9fzVhX",
        client_secret="03eEBjdLhbcZRoqqpYsjISmL7Gm635WHx9leKoIIWp0SGJ9Bfi6keRCpcWaqoI7ioyCLh64xn1pQj7TGpnG92jEhuWmrp10JXr6y7fHoT3vQaeR7MEaDfFdDb1Sa0HIZ",
        code_verifier=mock.ANY,  # Unpredictable due to secrets.token_urlsafe
        verify=False,
    )

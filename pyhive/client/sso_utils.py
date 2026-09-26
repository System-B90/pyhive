"""
Name: sso_utils.py
Purpose: Provide silent SSO authentication utilities for the PyHive client via OIDC.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import base64
import hashlib
import logging
import secrets
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from threading import Thread
from typing import TYPE_CHECKING, Any

import flask
import httpx

if TYPE_CHECKING:
    from . import HiveClient

LOCAL_SERVER_PORT = 8180
REQUIRED_SCOPES = "openid profile clearance extended_profile api"
HIVE_SSO_CLIENT_ID = "hive-local-sso-service"
HIVE_SSO_CLIENT_SECRET = "hive-local-sso-secret"

log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
flask_log = logging.getLogger("flask.app")
flask_log.setLevel(logging.ERROR)


def _generate_pkce_pair() -> tuple[str, str]:
    """
    Generates a cryptographically secure PKCE verifier and challenge pair.

    Returns:
        Tuple[str, str]: A tuple containing the code verifier and the S256 code challenge.
    """
    verifier = secrets.token_urlsafe(64)
    sha256_hash = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")
    return verifier, challenge


def _exchange_code_for_token(
    hive_url: str,
    auth_code: str,
    code_verifier: str,
    verify: bool | str | None = None,
) -> tuple[str, str, datetime]:
    """
    Exchanges an OAuth2 authorization code for a SimpleJWT token pair via the Hive SSO exchange endpoint.

    Args:
        hive_url (str): The base URL of the Hive server.
        auth_code (str): The authorization code returned from the initial OIDC login flow.
        code_verifier (str): The PKCE code verifier string generated prior to authorization.
        verify (Optional[Union[bool, str]]): SSL verification configuration for the HTTP client.
            Can be a boolean to enable/disable verification, or a string path to a CA bundle. Defaults to None.

    Returns:
        Tuple[str, str, datetime]: A tuple containing the JWT access token, the JWT refresh token,
            and a timezone-aware UTC datetime object representing the access token's expiration.

    Raises:
        RuntimeError: If the HTTP request for the token exchange or the SSO token exchange fails,
            or if the response is not valid JSON.
        ValueError: If the required opaque token is missing from the initial response, or if the
            JWT access token, refresh token, or expiration timestamp are missing from the exchange response.
    """
    token_url = f"{hive_url}/api/core/sso/token/"
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": f"http://localhost:{LOCAL_SERVER_PORT}/callback",
        "code_verifier": code_verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    ssl_verify = True if verify is None else verify

    with httpx.Client(verify=ssl_verify, follow_redirects=True) as client:
        response = client.post(
            token_url,
            data=payload,
            headers=headers,
            auth=(HIVE_SSO_CLIENT_ID, HIVE_SSO_CLIENT_SECRET),
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Token exchange failed (HTTP {response.status_code}): {response.text}"
            )

        token_data: dict[str, Any] = response.json()
        if not isinstance(token_data, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise TypeError("Token response did not return a JSON object")

        opaque_access_token = token_data.get("access_token")

        if not opaque_access_token:
            raise ValueError("Token response did not contain an 'access_token'.")

        exchange_url = f"{hive_url}/api/core/sso/exchange/"
        exchange_headers = {
            "Authorization": f"Bearer {opaque_access_token}",
            "Content-Type": "application/json",
        }

        exchange_response = client.post(
            exchange_url,
            headers=exchange_headers,
        )

        if exchange_response.status_code != 200:
            raise RuntimeError(
                f"SSO Token Exchange failed (HTTP {exchange_response.status_code}): {exchange_response.text}"
            )

        exchange_data: dict[str, Any] = exchange_response.json()
        jwt_access_token = exchange_data.get("access_token")
        jwt_refresh_token = exchange_data.get("refresh_token")
        expires_at_timestamp = exchange_data.get("expires_at")

        if (
            not jwt_access_token
            or not jwt_refresh_token
            or expires_at_timestamp is None
        ):
            raise ValueError(
                "Exchange response is missing 'access_token', 'refresh_token', or 'expires_at'."
            )

        expires_at_dt = datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc)

        return str(jwt_access_token), str(jwt_refresh_token), expires_at_dt


def _start_local_callback_server(
    hive_url: str,
    code_verifier: str,
    verify: bool | str | None = None,
) -> tuple[str, str, datetime]:
    """
    Spins up a temporary local Flask server to catch the OIDC callback, then exchanges the code.

    Args:
        hive_url (str): The base URL of the Hive server.
        code_verifier (str): The PKCE code verifier generated for this login session.
        verify (Optional[Union[bool, str]]): SSL verification configuration for the HTTP client. Defaults to None.

    Returns:
        Tuple[str, str, datetime]: The JWT access token, refresh token, and expiration datetime.

    Raises:
        PermissionError: If the OIDC flow returns an error in the callback state.
        RuntimeError: If no authorization code is present in the successful callback.
    """
    app = flask.Flask(__name__)
    flask.cli.show_server_banner = (  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        lambda *args, **kwargs: None  # pyright: ignore[reportUnknownLambdaType]
    )

    state: dict[str, Any] = {
        "auth_code": None,
        "error": None,
        "error_desc": None,
        "complete": False,
    }

    @app.route("/callback")
    def callback() -> str | tuple[str, int]:  # pyright: ignore[reportUnusedFunction]
        state["error"] = flask.request.args.get("error")
        state["error_desc"] = flask.request.args.get("error_description")
        state["auth_code"] = flask.request.args.get("code")
        state["complete"] = True
        if state["error"]:
            return (
                f"<h1>Auth Error</h1><p>{state['error']}: {state['error_desc']}</p>",
                400,
            )
        return "<h1>Success</h1><p>Authentication successful!</p>"

    server_thread = Thread(
        target=app.run,
        kwargs={"port": LOCAL_SERVER_PORT, "debug": False, "use_reloader": False},
    )
    server_thread.daemon = True
    server_thread.start()

    while not state["complete"]:
        time.sleep(0.2)

    if state["error"]:
        raise PermissionError(f"OIDC Error: {state['error']} - {state['error_desc']}")

    if not state["auth_code"]:
        raise RuntimeError("No authorization code returned from the SSO provider.")

    return _exchange_code_for_token(
        hive_url=hive_url,
        auth_code=state["auth_code"],
        code_verifier=code_verifier,
        verify=verify,
    )


def get_sso_token(
    hive_url: str, verify: bool | str | None = None
) -> tuple[str, str, datetime]:
    """
    Orchestrates the local Single Sign-On flow by opening a browser and catching the callback.

    Args:
        hive_url (str): The base URL of the Hive server.
        verify (Optional[Union[bool, str]]): SSL verification configuration. Defaults to None.

    Returns:
        Tuple[str, str, datetime]: The JWT access token, refresh token, and expiration datetime.
    """
    verifier, challenge = _generate_pkce_pair()
    params = {
        "client_id": HIVE_SSO_CLIENT_ID,
        "response_type": "code",
        "scope": REQUIRED_SCOPES,
        "redirect_uri": f"http://localhost:{LOCAL_SERVER_PORT}/callback",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    webbrowser.open(
        f"{hive_url}/api/core/sso/authorize?{urllib.parse.urlencode(params)}"
    )
    return _start_local_callback_server(
        hive_url=hive_url,
        code_verifier=verifier,
        verify=verify,
    )


def generate_sso_client_credentials(
    client: "HiveClient",
    service_name: str,
    redirect_uris: list[str] | str | None = None,
) -> dict[str, Any]:
    """
    Programmatically generates OAuth2 client credentials in Hive for a new external service.

    Args:
        client (HiveClient): An authenticated HiveClient instance.
        service_name (str): The name of the service requesting credentials.
        redirect_uris (Optional[List[str] | str]): A list of authorized redirect URIs. Defaults to None.

    Returns:
        dict[str, Any]: A dictionary containing the newly generated application's client_id, client_secret, and details.
    """
    if isinstance(redirect_uris, str):
        redirect_uris = [redirect_uris]

    response = client.post(
        "/api/core/sso/applications/",
        data={
            "name": service_name,
            "redirect_uris": " ".join(redirect_uris if redirect_uris else []),
        },
    )
    return {
        "id": response["id"],
        "name": response["name"],
        "owner": response["owner"],
        "redirect_uris": response["redirect_uris"],
        "skip_authorization": response["skip_authorization"],
        "client_id": response["client_id"],
        "client_secret": response["client_secret"],
    }

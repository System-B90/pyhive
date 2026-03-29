"""
Name: sso_utils.py
Purpose: Provide silent SSO authentication utilities for the PyHive client via OIDC.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import base64
import hashlib
import json
import logging
import secrets
import time
import urllib.parse
import webbrowser
from threading import Thread
from typing import Any, Dict, Optional, Tuple, Union

import flask
import httpx

LOCAL_SERVER_PORT = 8180
REQUIRED_SCOPES = "openid profile clearance extended_profile api"
HIVE_SSO_CLIENT_ID = "hive-local-sso-service"
HIVE_SSO_CLIENT_SECRET = "hive-local-sso-secret"

# Completely silence Werkzeug and Flask startup messages
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)
flask_log = logging.getLogger("flask.app")
flask_log.setLevel(logging.ERROR)


def _decode_jwt_payload(jwt_string: str) -> Dict[str, Any]:
    parts = jwt_string.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT structure returned by OIDC provider.")

    payload_b64 = parts[1]
    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
    payload_bytes = base64.urlsafe_b64decode(payload_b64)
    return json.loads(payload_bytes.decode("utf-8"))


def _generate_pkce_pair() -> Tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    sha256_hash = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")
    return verifier, challenge


def _start_local_callback_server(
    hive_url: str,
    client_id: str,
    client_secret: str,
    code_verifier: str,
    verify: Optional[Union[bool, str]] = None,
) -> str:
    app = flask.Flask(__name__)

    # This prevents Flask from printing the banner when app.run is called
    flask.cli.show_server_banner = lambda *args, **kwargs: None

    state = {
        "auth_code": None,
        "error": None,
        "error_desc": None,
        "complete": False,
    }

    @app.route("/callback")
    def callback():
        state["error"] = flask.request.args.get("error")
        state["error_desc"] = flask.request.args.get("error_description")
        state["auth_code"] = flask.request.args.get("code")
        state["complete"] = True

        if state["error"]:
            return (
                f"<h1>Authentication Error</h1><p>{state['error']}: {state['error_desc']}</p>",
                400,
            )
        return (
            "<h1>Success</h1><p>Authentication successful! You may close this tab.</p>"
        )

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

    token_url = f"{hive_url}/sso/token/"
    payload = {
        "grant_type": "authorization_code",
        "code": state["auth_code"],
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
            auth=(client_id, client_secret),
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Token exchange failed (HTTP {response.status_code}): {response.text}"
            )

        token_data = response.json()
        id_token = token_data.get("id_token")

        if not id_token:
            raise ValueError("Token response did not contain an 'id_token'.")

        profile_data = _decode_jwt_payload(id_token)
        api_token = profile_data.get("api_token")

        if not api_token:
            raise ValueError(
                "The ID token does not contain the 'api_token' claim. Verify scopes and Hive server configuration."
            )

        return api_token


def get_sso_token(hive_url: str, verify: Optional[Union[bool, str]] = None) -> str:
    verifier, challenge = _generate_pkce_pair()

    redirect_uri = f"http://localhost:{LOCAL_SERVER_PORT}/callback"
    params = {
        "client_id": HIVE_SSO_CLIENT_ID,
        "response_type": "code",
        "scope": REQUIRED_SCOPES,
        "redirect_uri": redirect_uri,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }

    query_string = urllib.parse.urlencode(params)
    sso_url = f"{hive_url}/sso/authorize?{query_string}"

    webbrowser.open(sso_url)

    return _start_local_callback_server(
        hive_url=hive_url,
        client_id=HIVE_SSO_CLIENT_ID,
        client_secret=HIVE_SSO_CLIENT_SECRET,
        code_verifier=verifier,
        verify=verify,
    )

"""
Name: client_factory.py
Purpose: Centralized instantiation of the HiveClient based on CLI state, environment, and OS Keyring.
Created: 2026-04-07
Author: Michael K. Steinberg
"""

import os

import keyring

from pyhive.cli.state import state
from pyhive.client import HiveClient

KEYRING_SERVICE = "pyhive_cli"
KEYRING_ACCOUNT = "pyhive_access_token"
KEYRING_REFRESH_ACCOUNT = "pyhive_refresh_token"


def _get_cached_tokens() -> tuple[str | None, str | None]:
    """Safely fetch the cached access and refresh tokens from the OS keyring."""
    try:
        access_token = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCOUNT)
        refresh_token = keyring.get_password(KEYRING_SERVICE, KEYRING_REFRESH_ACCOUNT)
    except Exception:  # pylint: disable=broad-exception-caught
        return None, None
    return access_token, refresh_token


def get_hive_client(hive_url: str, verify: bool) -> HiveClient:
    """
    Instantiate HiveClient using credentials from the global state, environment, or OS keyring.
    Prioritizes Username/Password, then explicit CLI Token, then Environment Variable,
    then OS Keyring, and finally falls back to SSO.

    Args:
        hive_url (str): The base URL of the Hive instance.
        verify (bool): Whether to verify SSL certificates.

    Returns:
        HiveClient: An authenticated instance of the Hive client.
    """
    env_token: str | None = os.environ.get("HIVE_ACCESS_TOKEN")
    keyring_access_token, keyring_refresh_token = _get_cached_tokens()

    if state.username and state.password:
        client = HiveClient(
            hive_url=hive_url,
            verify=verify,
            username=state.username,
            password=state.password,
        )
    elif state.access_token:
        client = HiveClient.from_api_token(
            hive_url=hive_url,
            verify=verify,
            api_token=state.access_token,
        )
    elif env_token:
        client = HiveClient.from_api_token(
            hive_url=hive_url,
            verify=verify,
            api_token=env_token,
        )
    elif keyring_access_token and keyring_refresh_token:
        client = HiveClient.from_api_token(
            hive_url=hive_url,
            verify=verify,
            api_token=keyring_access_token,
            refresh_token=keyring_refresh_token,
            auth_strategy="cache",
        )
    else:
        client = HiveClient.from_sso(
            hive_url=hive_url,
            verify=verify,
        )

    if state.cache_token:
        access_token: str | None = client._access_token  # pylint: disable=protected-access
        refresh_token: str | None = client._refresh_token  # pylint: disable=protected-access
        if access_token:
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, access_token)
                if refresh_token:
                    keyring.set_password(
                        KEYRING_SERVICE, KEYRING_REFRESH_ACCOUNT, refresh_token
                    )
            except Exception:  # pylint: disable=broad-exception-caught
                # Silently fail or log in debug mode; we don't want to crash
                # the command execution just because the keychain is locked
                pass

    return client

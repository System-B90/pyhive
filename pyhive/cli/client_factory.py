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

    # Safely attempt to fetch from OS credential manager
    try:
        keyring_token: str | None = keyring.get_password(
            KEYRING_SERVICE, KEYRING_ACCOUNT
        )
    except Exception:  # pylint: disable=broad-exception-caught
        keyring_token = None

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
    elif keyring_token:
        client = HiveClient.from_api_token(
            hive_url=hive_url,
            verify=verify,
            api_token=keyring_token,
        )
    else:
        client = HiveClient.from_sso(
            hive_url=hive_url,
            verify=verify,
        )

    if state.cache_token:
        token: str | None = client._access_token  # pylint: disable=protected-access
        if token:
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, token)
            except Exception:  # pylint: disable=broad-exception-caught
                # Silently fail or log in debug mode; we don't want to crash
                # the command execution just because the keychain is locked
                pass

    return client

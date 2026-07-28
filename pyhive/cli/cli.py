"""
Name: cli.py
Purpose: PyHive CLI entry point providing utility commands
         including SSO token generation,
         service registration, and version info.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import importlib.metadata
from datetime import datetime
from typing import Any

import keyring
import typer

from pyhive.cli.assignments import assignment_app
from pyhive.cli.base import PyHiveTyper
from pyhive.cli.classes import class_app
from pyhive.cli.client_factory import (
    KEYRING_ACCOUNT,
    KEYRING_REFRESH_ACCOUNT,
    KEYRING_SERVICE,
    get_hive_client,
)
from pyhive.cli.exercises import exercise_app
from pyhive.cli.formatter import print_error_and_exit, print_info, print_result
from pyhive.cli.modules import module_app
from pyhive.cli.programs import program_app
from pyhive.cli.state import state
from pyhive.cli.subjects import subject_app
from pyhive.cli.users import user_app
from pyhive.client.sso_utils import get_sso_token
from pyhive.src._generated_versions import SUPPORTED_API_VERSIONS

app = PyHiveTyper(help="PyHive CLI", rich_markup_mode="rich", no_args_is_help=True)

app.add_typer(assignment_app, name="assignments")
app.add_typer(class_app, name="classes")
app.add_typer(exercise_app, name="exercises")
app.add_typer(module_app, name="modules")
app.add_typer(program_app, name="programs")
app.add_typer(subject_app, name="subjects")
app.add_typer(user_app, name="users")


@app.callback()
def main_callback(
    username: str | None = typer.Option(
        None, "--username", "-u", help="Hive username for authentication"
    ),
    password: str | None = typer.Option(
        None, "--password", "-p", help="Hive password for authentication"
    ),
    access_token: str | None = typer.Option(
        None, "--token", "-t", help="Hive access token for authentication"
    ),
) -> None:
    """Store root-level auth credentials into global CLI state."""
    state.username = username
    state.password = password
    state.access_token = access_token

    if state.cache_token:
        print_info(
            "WARNING: Token caching is enabled. This is a security risk. Only use this flag on a trusted machine.",
            fg=typer.colors.RED,
        )


@app.command(name="version")
def show_version() -> None:
    """
    Show the current version of the PyHive package.

    Args:
        None

    Returns:
        None
    """
    try:
        version_str: str = importlib.metadata.version("PyHiveLMS")
    except importlib.metadata.PackageNotFoundError:
        version_str = "unknown"

    def text_output() -> None:
        typer.echo(f"PyHive CLI Version: {version_str}")

    print_result({"pyhive_version": version_str}, text_output)


@app.command()
def versions() -> None:
    """
    Show supported Hive API versions.

    Args:
        None

    Returns:
        None
    """

    def text_output() -> None:
        typer.echo("Supported Hive Versions:")
        for v in SUPPORTED_API_VERSIONS:
            typer.echo(v)

    print_result({"versions": SUPPORTED_API_VERSIONS}, text_output)


@app.command(name="token")
def get_token(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """
    Authenticate via SSO and output a valid access token.

    Args:
        hive_url (str): The base URL of the Hive instance.
        verify (bool): Whether to verify SSL certificates during token exchange.

    Returns:
        None
    """
    try:
        print_info(f"Initiating SSO authentication for {hive_url}...")
        access_token: str
        refresh_token: str
        expires_at: datetime
        access_token, refresh_token, expires_at = get_sso_token(
            hive_url=hive_url, verify=verify
        )

        if state.cache_token:
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_ACCOUNT, access_token)
                keyring.set_password(
                    KEYRING_SERVICE, KEYRING_REFRESH_ACCOUNT, refresh_token
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                # A locked or unavailable keychain must not fail the command —
                # the token in hand is still valid. But swallowing it silently
                # left users with no way to tell caching had failed. stderr, so
                # --json output stays machine-parseable.
                typer.secho(
                    f"Warning: could not cache token in the OS keyring ({exc}).",
                    fg=typer.colors.YELLOW,
                    err=True,
                )

        def text_output() -> None:
            typer.secho("\nAuthentication Successful!", fg=typer.colors.GREEN)
            typer.echo(f"Access Token: {access_token}")

        payload: dict[str, Any] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
        print_result(payload, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Authentication failed: {e}",
            error_data={"error": "Authentication failed", "details": str(e)},
        )


@app.command(name="register")
def register_service(
    service_name: str = typer.Argument(..., help="Name of the service to register"),
    redirect_uri: str = typer.Argument(
        ...,
        help="Redirect URI for the service (optional) (e.g. http://localhost:5000/api/auth/callback/hive)",
    ),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """
    Register a new service with the Hive server and generate client keys.

    Args:
        service_name (str): The name of the service being registered.
        redirect_uri (str): Redirect URI for the service after authentication.
        hive_url (str): The base URL of the Hive instance.
        verify (bool): Whether to verify SSL certificates during registration.

    Returns:
        None
    """
    try:
        print_info(f"Registering service '{service_name}' at {hive_url}...")

        client = get_hive_client(hive_url=hive_url, verify=verify)
        keys: dict[str, Any] = client.register_sso_service(
            service_name=service_name, redirect_uris=redirect_uri
        )

        client_id: str = keys.get("client_id", "N/A")
        client_secret: str = keys.get("client_secret", "N/A")
        owner: str = keys.get("owner", "Anonymous")
        skip_authorization: bool = keys.get("skip_authorization", False)

        def text_output() -> None:
            typer.secho("\nService Registration Successful!", fg=typer.colors.GREEN)
            typer.echo(f"Client ID: {client_id}")
            typer.echo(f"Client Secret: {client_secret}")
            typer.echo(f"Owner: {owner}")
            typer.echo(f"User Authorization Required: {not skip_authorization}")

        payload: dict[str, Any] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "owner": owner,
            "skip_authorization": skip_authorization,
        }
        print_result(payload, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Service registration failed: {e}",
            error_data={"error": "Service registration failed", "details": str(e)},
        )


def main() -> None:
    """
    PyHive CLI main entry point.

    Args:
        None

    Returns:
        None
    """
    app()


if __name__ == "__main__":
    main()

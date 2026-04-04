"""
Name: cli.py
Purpose: PyHive CLI entry point providing utility commands including SSO token generation and service registration.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import typer

from pyhive.client import HiveClient
from pyhive.client.sso_utils import get_sso_token
from pyhive.src._generated_versions import SUPPORTED_API_VERSIONS

app = typer.Typer(help="PyHive CLI")


@app.command()
def versions() -> None:
    """
    Show supported Hive versions.

    Args:
        None

    Returns:
        None
    """
    typer.echo("Supported Hive Versions:")
    for v in SUPPORTED_API_VERSIONS:
        typer.echo(v)


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
        typer.echo(f"Initiating SSO authentication for {hive_url}...")
        access_token = get_sso_token(hive_url=hive_url, verify=verify)
        typer.secho("\nAuthentication Successful!", fg=typer.colors.GREEN)
        typer.echo(f"Access Token: {access_token}")
    except Exception as e:
        typer.secho(f"\nAuthentication failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


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
        typer.echo(f"Registering service '{service_name}' at {hive_url}...")

        client = HiveClient.from_sso(hive_url=hive_url, verify=verify)
        # Generates keys dynamically via the client module
        keys = client.register_sso_service(
            service_name=service_name, redirect_uris=redirect_uri
        )

        client_id = keys.get("client_id", "N/A")
        client_secret = keys.get("client_secret", "N/A")
        owner = keys.get("owner", "Anonymous")
        skip_authorization = keys.get("skip_authorization", False)

        typer.secho("\nService Registration Successful!", fg=typer.colors.GREEN)
        typer.echo(f"Client ID: {client_id}")
        typer.echo(f"Client Secret: {client_secret}")
        typer.echo(f"Owner: {owner}")
        typer.echo(f"User Authorization Required: {not skip_authorization}")
    except Exception as e:
        typer.secho(f"\nService registration failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


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

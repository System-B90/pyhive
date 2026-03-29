"""
Name: cli.py
Purpose: PyHive CLI entry point providing utility commands including SSO token generation.
Created: 2026-03-29
Author: Michael K. Steinberg
"""

import typer

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

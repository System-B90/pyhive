"""
Name: formatter.py
Purpose: Utility functions for standardizing CLI text and JSON output using Python 3.10+ typing.
Created: 2026-04-07
Author: Michael K. Steinberg
"""

import json
from collections.abc import Callable
from typing import Any

import typer

from pyhive.cli.state import state


def print_info(message: str, fg: str | None = None) -> None:
    """
    Print informational messages to standard output if JSON mode is disabled.

    Args:
        message (str): The text message to display.
        fg (str | None): The Typer color string for the text. Defaults to None.

    Returns:
        None
    """
    if not state.use_json:
        typer.secho(message, fg=fg)


def print_result(data: dict[str, Any], text_fallback: Callable[[], None]) -> None:
    """
    Print the final command result as JSON to stdout, or execute the text fallback.

    Args:
        data (dict[str, Any]): The structured data payload for JSON output.
        text_fallback (Callable[[], None]): The function to call for standard text output.

    Returns:
        None
    """
    if state.use_json:
        typer.echo(json.dumps(data, indent=2))
    else:
        text_fallback()


def print_error_and_exit(
    message: str, error_data: dict[str, Any] | None = None
) -> None:
    """
    Print an error message and exit the CLI with a non-zero status code.

    Args:
        message (str): The error message text.
        error_data (dict[str, Any] | None): Structured error data for JSON mode. Defaults to None.

    Returns:
        None
    """
    if state.use_json:
        payload: dict[str, Any] = (
            error_data if error_data is not None else {"error": message}
        )
        typer.echo(json.dumps(payload, indent=2), err=True)
        raise typer.Exit(code=1)

    typer.secho(f"\nError: {message}", fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


def print_formatted_list(
    data: list[dict[str, Any]], template: str, keys: list[str]
) -> None:
    """
    Print a list of dictionaries with dynamic column alignment.

    Args:
        data (list[dict[str, Any]]): The dataset to print.
        template (str): String with placeholders (e.g., "- [{id}] ({number}) {name}").
        keys (list[str]): The keys to calculate max widths for.

    Returns:
        None
    """
    if not data:
        return

    # Calculate max width for each key across all items
    widths: dict[str, int] = {
        key: max(len(str(item.get(key, ""))) for item in data) for key in keys
    }

    for item in data:
        # Construct padded values
        padded_values = {
            key: str(item.get(key, "None")).rjust(widths[key]) for key in keys
        }
        typer.echo(template.format(**padded_values))

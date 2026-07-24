"""Subjects CLI subcommand group."""

from typing import Any

import typer

from pyhive.cli.base import PyHiveTyper
from pyhive.cli.client_factory import get_hive_client
from pyhive.cli.formatter import (
    print_error_and_exit,
    print_formatted_list,
    print_info,
    print_result,
)

subject_app = PyHiveTyper(help="Manage Hive subjects.")


@subject_app.callback(invoke_without_command=True)
def subject_callback(
    ctx: typer.Context,
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_subjects(hive_url=hive_url, verify=verify)


@subject_app.command(name="list")
def list_subjects(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """List all subjects."""
    try:
        print_info(f"Fetching subjects from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)
        subjects = sorted(
            [x.to_dict() for x in client.get_subjects()], key=lambda x: x["id"]
        )

        def text_output() -> None:
            typer.secho(f"\nFound {len(subjects)} subjects:", fg=typer.colors.GREEN)
            print_formatted_list(
                data=subjects,
                template="- [{id}]  [{symbol}]  {name}",
                keys=["id", "symbol", "name"],
            )

        print_result({"subjects": subjects}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to fetch subjects: {e}",
            error_data={"error": "Subject fetch failed", "details": str(e)},
        )


@subject_app.command(name="get")
def get_subject(
    subject_id: int = typer.Argument(..., help="ID of the subject"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Get a subject by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        subject = client.get_subject(subject_id)
        data: dict[str, Any] = subject.to_dict()

        def text_output() -> None:
            for key, value in data.items():
                typer.echo(f"{key}: {value}")

        print_result({"subject": data}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to get subject {subject_id}: {e}",
            error_data={"error": "Subject get failed", "details": str(e)},
        )


@subject_app.command(name="delete")
def delete_subject(
    subject_id: int = typer.Argument(..., help="ID of the subject to delete"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Delete a subject by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        client.delete_subject(subject_id)

        def text_output() -> None:
            typer.secho(f"\nSubject '{subject_id}' deleted.", fg=typer.colors.GREEN)

        print_result({"deleted_subject_id": subject_id, "status": "success"}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to delete subject {subject_id}: {e}",
            error_data={"error": "Subject deletion failed", "details": str(e)},
        )

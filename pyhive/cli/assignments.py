"""Assignments CLI subcommand group."""

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

assignment_app = PyHiveTyper(help="Manage Hive assignments.")


@assignment_app.callback(invoke_without_command=True)
def assignment_callback(
    ctx: typer.Context,
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_assignments(hive_url=hive_url, verify=verify)


@assignment_app.command(name="list")
def list_assignments(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """List all assignments."""
    try:
        print_info(f"Fetching assignments from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)
        assignments = sorted(
            [x.to_dict() for x in client.get_assignments()], key=lambda x: x["id"]
        )

        def text_output() -> None:
            typer.secho(f"\nFound {len(assignments)} assignments:", fg=typer.colors.GREEN)
            print_formatted_list(
                data=assignments,
                template="- [{id}]  user:{user}  ex:{exercise}  {assignment_status}",
                keys=["id", "user", "exercise", "assignment_status"],
            )

        print_result({"assignments": assignments}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to fetch assignments: {e}",
            error_data={"error": "Assignment fetch failed", "details": str(e)},
        )


@assignment_app.command(name="get")
def get_assignment(
    assignment_id: int = typer.Argument(..., help="ID of the assignment"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Get an assignment by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        assignment = client.get_assignment(assignment_id)
        data: dict[str, Any] = assignment.to_dict()

        def text_output() -> None:
            for key, value in data.items():
                typer.echo(f"{key}: {value}")

        print_result({"assignment": data}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to get assignment {assignment_id}: {e}",
            error_data={"error": "Assignment get failed", "details": str(e)},
        )

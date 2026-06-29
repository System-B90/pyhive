"""Programs CLI subcommand group."""

from typing import Any

import typer

from pyhive.cli.base import PyHiveTyper
from pyhive.cli.client_factory import get_hive_client
from pyhive.cli.formatter import print_error_and_exit, print_formatted_list, print_info, print_result

program_app = PyHiveTyper(help="Manage Hive programs.")


@program_app.callback(invoke_without_command=True)
def program_callback(
    ctx: typer.Context,
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_programs(hive_url=hive_url, verify=verify)


@program_app.command(name="list")
def list_programs(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """List all programs."""
    try:
        print_info(f"Fetching programs from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)
        programs = sorted(
            [x.to_dict() for x in client.get_programs()], key=lambda x: x["id"]
        )

        def text_output() -> None:
            typer.secho(f"\nFound {len(programs)} programs:", fg=typer.colors.GREEN)
            print_formatted_list(
                data=programs,
                template="- [{id}]  {name}  (checker: {checker})",
                keys=["id", "name", "checker"],
            )

        print_result({"programs": programs}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to fetch programs: {e}",
            error_data={"error": "Program fetch failed", "details": str(e)},
        )


@program_app.command(name="get")
def get_program(
    program_id: int = typer.Argument(..., help="ID of the program"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Get a program by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        program = client.get_program(program_id)
        data: dict[str, Any] = program.to_dict()

        def text_output() -> None:
            for key, value in data.items():
                typer.echo(f"{key}: {value}")

        print_result({"program": data}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to get program {program_id}: {e}",
            error_data={"error": "Program get failed", "details": str(e)},
        )


@program_app.command(name="delete")
def delete_program(
    program_id: int = typer.Argument(..., help="ID of the program to delete"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Delete a program by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        client.delete_program(program_id)

        def text_output() -> None:
            typer.secho(f"\nProgram '{program_id}' deleted.", fg=typer.colors.GREEN)

        print_result({"deleted_program_id": program_id, "status": "success"}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to delete program {program_id}: {e}",
            error_data={"error": "Program deletion failed", "details": str(e)},
        )

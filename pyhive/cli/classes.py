"""Classes CLI subcommand group."""

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

class_app = PyHiveTyper(help="Manage Hive classes.")


@class_app.callback(invoke_without_command=True)
def class_callback(
    ctx: typer.Context,
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_classes(hive_url=hive_url, verify=verify)


@class_app.command(name="list")
def list_classes(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """List all classes."""
    try:
        print_info(f"Fetching classes from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)
        classes = sorted(
            [x.to_dict() for x in client.get_classes()], key=lambda x: x["id"]
        )

        def text_output() -> None:
            typer.secho(f"\nFound {len(classes)} classes:", fg=typer.colors.GREEN)
            print_formatted_list(
                data=classes,
                template="- [{id}]  {name}  (program: {program})",
                keys=["id", "name", "program"],
            )

        print_result({"classes": classes}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to fetch classes: {e}",
            error_data={"error": "Class fetch failed", "details": str(e)},
        )


@class_app.command(name="get")
def get_class(
    class_id: int = typer.Argument(..., help="ID of the class"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Get a class by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        hive_class = client.get_class(class_id)
        data: dict[str, Any] = hive_class.to_dict()

        def text_output() -> None:
            for key, value in data.items():
                typer.echo(f"{key}: {value}")

        print_result({"class": data}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to get class {class_id}: {e}",
            error_data={"error": "Class get failed", "details": str(e)},
        )


@class_app.command(name="delete")
def delete_class(
    class_id: int = typer.Argument(..., help="ID of the class to delete"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Delete a class by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        client.delete_class(class_id)

        def text_output() -> None:
            typer.secho(f"\nClass '{class_id}' deleted.", fg=typer.colors.GREEN)

        print_result({"deleted_class_id": class_id, "status": "success"}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to delete class {class_id}: {e}",
            error_data={"error": "Class deletion failed", "details": str(e)},
        )

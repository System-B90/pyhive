"""Modules CLI subcommand group."""

from typing import Any

import typer

from pyhive.cli.base import PyHiveTyper
from pyhive.cli.client_factory import get_hive_client
from pyhive.cli.formatter import print_error_and_exit, print_formatted_list, print_info, print_result

module_app = PyHiveTyper(help="Manage Hive modules.")


@module_app.callback(invoke_without_command=True)
def module_callback(
    ctx: typer.Context,
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_modules(hive_url=hive_url, verify=verify)


@module_app.command(name="list")
def list_modules(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """List all modules."""
    try:
        print_info(f"Fetching modules from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)
        modules = sorted(
            [x.to_dict() for x in client.get_modules()], key=lambda x: x["id"]
        )

        def text_output() -> None:
            typer.secho(f"\nFound {len(modules)} modules:", fg=typer.colors.GREEN)
            print_formatted_list(
                data=modules,
                template="- [{id}]  {name}  (order: {order})",
                keys=["id", "name", "order"],
            )

        print_result({"modules": modules}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to fetch modules: {e}",
            error_data={"error": "Module fetch failed", "details": str(e)},
        )


@module_app.command(name="get")
def get_module(
    module_id: int = typer.Argument(..., help="ID of the module"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Get a module by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        module = client.get_module(module_id)
        data: dict[str, Any] = module.to_dict()

        def text_output() -> None:
            for key, value in data.items():
                typer.echo(f"{key}: {value}")

        print_result({"module": data}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to get module {module_id}: {e}",
            error_data={"error": "Module get failed", "details": str(e)},
        )


@module_app.command(name="delete")
def delete_module(
    module_id: int = typer.Argument(..., help="ID of the module to delete"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Delete a module by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        client.delete_module(module_id)

        def text_output() -> None:
            typer.secho(f"\nModule '{module_id}' deleted.", fg=typer.colors.GREEN)

        print_result({"deleted_module_id": module_id, "status": "success"}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to delete module {module_id}: {e}",
            error_data={"error": "Module deletion failed", "details": str(e)},
        )

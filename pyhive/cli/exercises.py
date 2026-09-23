"""Exercises CLI subcommand group."""

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

exercise_app = PyHiveTyper(help="Manage Hive exercises.")


@exercise_app.callback(invoke_without_command=True)
def exercise_callback(
    ctx: typer.Context,
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_exercises(hive_url=hive_url, verify=verify)


@exercise_app.command(name="list")
def list_exercises(
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """List all exercises."""
    try:
        print_info(f"Fetching exercises from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)
        exercises = sorted(
            [x.to_dict() for x in client.get_exercises()], key=lambda x: x["id"]
        )

        def text_output() -> None:
            typer.secho(f"\nFound {len(exercises)} exercises:", fg=typer.colors.GREEN)
            print_formatted_list(
                data=exercises,
                template="- [{id}]  [{parent_subject_symbol}]  {name}",
                keys=["id", "parent_subject_symbol", "name"],
            )

        print_result({"exercises": exercises}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to fetch exercises: {e}",
            error_data={"error": "Exercise fetch failed", "details": str(e)},
        )


@exercise_app.command(name="get")
def get_exercise(
    exercise_id: int = typer.Argument(..., help="ID of the exercise"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Get an exercise by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        exercise = client.get_exercise(exercise_id)
        data: dict[str, Any] = exercise.to_dict()

        def text_output() -> None:
            for key, value in data.items():
                typer.echo(f"{key}: {value}")

        print_result({"exercise": data}, text_output)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to get exercise {exercise_id}: {e}",
            error_data={"error": "Exercise get failed", "details": str(e)},
        )


@exercise_app.command(name="delete")
def delete_exercise(
    exercise_id: int = typer.Argument(..., help="ID of the exercise to delete"),
    hive_url: str = typer.Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = typer.Option(False, help="Verify SSL certificates"),
) -> None:
    """Delete an exercise by ID."""
    try:
        client = get_hive_client(hive_url=hive_url, verify=verify)
        client.delete_exercise(exercise_id)

        def text_output() -> None:
            typer.secho(f"\nExercise '{exercise_id}' deleted.", fg=typer.colors.GREEN)

        print_result(
            {"deleted_exercise_id": exercise_id, "status": "success"}, text_output
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        print_error_and_exit(
            message=f"Failed to delete exercise {exercise_id}: {e}",
            error_data={"error": "Exercise deletion failed", "details": str(e)},
        )

"""
Name: users.py
Purpose: User management CLI subparser for Hive utilizing RESTful CRUD operations.
Created: 2026-04-07
Author: Michael K. Steinberg
"""

from typing import Any

import click
from typer import (  # pyright: ignore[reportUnknownVariableType]
    Argument,
    Context,
    Option,
    colors,
    echo,
    secho,
)

from pyhive.cli.base import PyHiveTyper
from pyhive.cli.client_factory import get_hive_client
from pyhive.cli.formatter import (
    print_error_and_exit,
    print_formatted_list,
    print_info,
    print_result,
)
from pyhive.types import ClearanceEnum, GenderEnum, StatusEnum

user_app = PyHiveTyper(help="Manage Hive users.")


@user_app.callback(invoke_without_command=True)
def user_callback(
    ctx: Context,
    hive_url: str = Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = Option(False, help="Verify SSL certificates"),
) -> None:
    if ctx.invoked_subcommand is None:
        list_users(hive_url=hive_url, verify=verify)


@user_app.command(name="list")
def list_users(
    hive_url: str = Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = Option(False, help="Verify SSL certificates"),
) -> None:
    """
    Retrieve a list of users from the Hive server.

    Args:
        hive_url (str): The base URL of the Hive instance.
        verify (bool): Whether to verify SSL certificates.

    Returns:
        None
    """
    try:
        print_info(f"Fetching users from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)

        users = sorted([x.to_dict() for x in client.get_users()], key=lambda x: x["id"])

        def text_output() -> None:
            secho(f"\nFound {len(users)} users:", fg=colors.GREEN)
            print_formatted_list(
                data=users,
                template="- [{id}]  ({number})  {username}",
                keys=["id", "number", "username"],
            )

        print_result({"users": users}, text_output)

    except Exception as e:
        print_error_and_exit(
            message=f"Failed to fetch users: {e}",
            error_data={"error": "User fetch failed", "details": str(e)},
        )


@user_app.command(name="create")
def create_user(
    username: str = Argument(..., help="Username for the new account"),
    password: str = Option(
        ..., prompt=True, hide_input=True, help="Password for the account"
    ),
    clearance: str = Option(
        ...,
        help="Clearance level for the user.",
        click_type=click.Choice(list(ClearanceEnum.__members__), case_sensitive=False),
    ),
    gender: str = Option(
        ...,
        help="Gender of the user.",
        click_type=click.Choice(list(GenderEnum.__members__), case_sensitive=False),
    ),
    status: str = Option(
        StatusEnum.PRESENT.name,
        help="Initial user status.",
        click_type=click.Choice(list(StatusEnum.__members__), case_sensitive=False),
    ),
    number: int | None = Option(None, help="Identification number"),
    first_name: str | None = Option(None, help="User's first name"),
    last_name: str | None = Option(None, help="User's last name"),
    avatar_filename: str | None = Option(None, help="Avatar filename"),
    teacher: bool | None = Option(None, help="Set teacher status"),
    confirmed: bool | None = Option(None, help="Set confirmed status"),
    hive_url: str = Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = Option(False, help="Verify SSL certificates"),
) -> None:
    """
    Create a new user on the Hive server using Enum names for selection.

    Args:
        username (str): The username for the new account.
        password (str): Password for the account.
        clearance (str): The name of the clearance level.
        gender (str): The name of the gender.
        status (str): The name of the status.
        number (int | None): Identification number.
        first_name (str | None): User's first name.
        last_name (str | None): User's last name.
        avatar_filename (str | None): Avatar filename.
        teacher (bool | None): Set teacher status.
        confirmed (bool | None): Set confirmed status.
        hive_url (str): The base URL of the Hive instance.
        verify (bool): Whether to verify SSL certificates.

    Returns:
        None
    """
    try:
        print_info(f"Creating user '{username}' at {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)

        user = client.create_user(
            username=username,
            password=password,
            clearance=ClearanceEnum[clearance.upper()],
            gender=GenderEnum[gender.upper()],
            status=StatusEnum[status.upper()],
            number=number,
            first_name=first_name,
            last_name=last_name,
            avatar_filename=avatar_filename,
            teacher=teacher,
            confirmed=confirmed,
        )

        user_data: dict[str, Any] = getattr(user, "model_dump", lambda: vars(user))()

        def text_output() -> None:
            secho("\nUser successfully created!", fg=colors.GREEN)
            echo(f"ID: {getattr(user, 'id', 'N/A')}")
            echo(f"Username: {user.username}")
            echo(f"Clearance: {user.clearance.name}")

        print_result({"user": user_data, "status": "created"}, text_output)

    except Exception as e:
        print_error_and_exit(
            message=f"Failed to create user: {e}",
            error_data={"error": "User creation failed", "details": str(e)},
        )


@user_app.command(name="delete")
def delete_user(
    user_id: int = Argument(..., help="ID of the user to delete"),
    hive_url: str = Option("https://hive.org", help="Target Hive server URL"),
    verify: bool = Option(False, help="Verify SSL certificates"),
) -> None:
    """
    Delete an existing user from the Hive server.

    Args:
        user_id (str): The ID of the user to remove.
        hive_url (str): The base URL of the Hive instance.
        verify (bool): Whether to verify SSL certificates.

    Returns:
        None
    """
    try:
        print_info(f"Deleting user '{user_id}' from {hive_url}...")
        client = get_hive_client(hive_url=hive_url, verify=verify)

        success = True
        try:
            client.delete_user(user=user_id)
        except RuntimeError:
            success = False

        if not success:
            raise ValueError(f"User {user_id} could not be deleted or does not exist.")

        def text_output() -> None:
            secho(f"\nUser '{user_id}' successfully deleted.", fg=colors.GREEN)

        print_result({"deleted_user_id": user_id, "status": "success"}, text_output)

    except Exception as e:
        print_error_and_exit(
            message=f"Failed to delete user: {e}",
            error_data={"error": "User deletion failed", "details": str(e)},
        )

import sys
from typing import Any

import click
from click import echo
from pydantic import EmailStr
from rich import get_console
from rich.prompt import Confirm

from spannermc.domain.accounts.schemas import UserCreate, UserUpdate
from spannermc.domain.accounts.services import UserService
from spannermc.lib import db, log

__all__ = [
    "create_database",
    "create_user",
    "database_management_app",
    "promote_to_superuser",
    "purge_database",
    "reset_database",
    "show_database_revision",
    "upgrade_database",
    "user_management_app",
]


console = get_console()
"""Pre-configured CLI Console."""

logger = log.get_logger()


@click.group(name="database", invoke_without_command=False, help="Manage the configured database backend.")
@click.pass_context
def database_management_app(_: dict[str, Any]) -> None:
    """Manage the configured database backend."""


@click.group(name="users", invoke_without_command=False, help="Manage application users.")
@click.pass_context
def user_management_app(_: dict[str, Any]) -> None:
    """Manage application users."""


@user_management_app.command(name="create-user", help="Create a user")
@click.option(
    "--email",
    help="Email of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--name",
    help="Full name of the new user",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--password",
    help="Password",
    type=click.STRING,
    required=False,
    show_default=False,
)
@click.option(
    "--superuser",
    help="Is a superuser",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=False,
    is_flag=True,
)
def create_user(
    email: str | None,
    name: str | None,
    password: str | None,
    superuser: bool | None,
) -> None:
    """Create a user."""

    def _create_user(
        email: str,
        name: str,
        password: str,
        superuser: bool = False,
    ) -> None:
        obj_in = UserCreate(
            email=EmailStr(email),
            name=name,
            password=password,
            is_superuser=superuser,
        )

        with UserService.new() as users_service:
            user = users_service.create(data=obj_in.__dict__)
            users_service.repository.session.commit()
            logger.info("User created: %s", user.email)

    email = email or click.prompt("Email")
    name = name or click.prompt("Full Name", show_default=False)
    password = password or click.prompt("Password", hide_input=True, confirmation_prompt=True)
    superuser = superuser or click.prompt("Create as superuser?", show_default=True, type=click.BOOL)

    _create_user(email, name, password, superuser)


@user_management_app.command(name="promote-to-superuser", help="Promotes a user to application superuser")
@click.option(
    "--email",
    help="Email of the user",
    type=click.STRING,
    required=False,
    show_default=False,
)
def promote_to_superuser(email: str) -> None:
    """Promote to Superuser.

    Args:
        email (str): _description_
    """

    def _promote_to_superuser(email: str) -> None:
        with UserService.new() as users_service:
            user = users_service.get_one_or_none(email=email)
            if user:
                logger.info("Promoting user: %s", user.email)
                user_in = UserUpdate(
                    email=user.email,
                    is_superuser=True,
                )
                user = users_service.update(
                    item_id=user.id,
                    data=user_in.__dict__,
                )
                users_service.repository.session.commit()
                logger.info("Upgraded %s to superuser", email)
            else:
                logger.warning("User not found: %s", email)

    _promote_to_superuser(email)


@database_management_app.command(
    name="create",
    help="Creates an empty postgres database and executes migrations",
)
def create_database() -> None:
    """Create database DDL migrations."""
    db.utils.create_database()


@database_management_app.command(
    name="upgrade",
    help="Executes migrations to apply any outstanding database structures.",
)
def upgrade_database() -> None:
    """Upgrade the database to the latest revision."""
    db.utils.upgrade_database()


@database_management_app.command(
    name="reset",
    help="Executes migrations to apply any outstanding database structures.",
)
@click.option(
    "--no-prompt",
    help="Do not prompt for confirmation.",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=True,
    is_flag=True,
)
def reset_database(no_prompt: bool) -> None:
    """Reset the database to an initial empty state."""
    if not no_prompt:
        Confirm.ask("Are you sure you want to drop and recreate everything?")
    db.utils.reset_database()


@database_management_app.command(
    name="purge",
    help="Drops all tables.",
)
@click.option(
    "--no-prompt",
    help="Do not prompt for confirmation.",
    type=click.BOOL,
    default=False,
    required=False,
    show_default=True,
    is_flag=True,
)
def purge_database(no_prompt: bool) -> None:
    """Drop all objects in the database."""
    if not no_prompt:
        confirmed = Confirm.ask(
            "Are you sure you want to drop everything?",
        )
        if not confirmed:
            echo("Aborting database purge and exiting.")
            sys.exit(0)
    db.utils.purge_database()


@database_management_app.command(
    name="show-current-revision",
    help="Shows the current revision for the database.",
)
def show_database_revision() -> None:
    """Show current database revision."""
    db.utils.show_database_revision()

import click
from flask.cli import AppGroup
from flask.cli import with_appcontext

from depc.controllers import NotFoundError
from depc.controllers.users import UserController

user_cli = AppGroup("user", help="Manage users.")


@user_cli.command("create")
@with_appcontext
@click.argument("name", default=None, required=True, type=str)
@click.option("--admin", default=False, required=False, type=bool, is_flag=True)
def create_user(name, admin):
    """Create a new user."""
    is_admin = bool(admin)
    try:
        user = UserController._get(filters={"User": {"name": name}})
        click.echo(
            "User {name} already exists with id: {id}".format(name=name, id=user.id)
        )
    except NotFoundError:
        click.confirm(
            "User {name} will be created with admin = {admin}".format(
                name=name, admin=is_admin
            ),
            abort=True,
        )
        UserController.create({"name": name, "active": True, "admin": is_admin})

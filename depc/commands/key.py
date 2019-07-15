import click
from flask import current_app as app
from flask.cli import AppGroup
from flask.cli import with_appcontext

from depc.extensions.encrypted_dict import FlaskEncryptedDict

key_cli = AppGroup("key", help="Manage database key.")


@key_cli.command("generate")
def generate_key():
    """Generate a 256-bit hex key to encrypt database."""
    click.echo(FlaskEncryptedDict.generate_key())


@key_cli.command("change")
@with_appcontext
@click.option("--old-key", default=None, required=True, type=str)
@click.option("--new-key", default=None, required=True, type=str)
def change_key(old_key, new_key):
    """Change the 256-bit hex key to encrypt database."""
    if old_key is None:
        old_key = app.config.get("DB_ENCRYPTION_KEY")

    FlaskEncryptedDict.change_key(old_key, new_key)
    click.echo("Database key has been changed")
    click.echo("Add this key to depc.{env}.yml as DB_ENCRYPTION_KEY")
    click.echo(new_key)

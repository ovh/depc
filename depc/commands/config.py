import click
import yaml
from flask import current_app as app
from flask.cli import AppGroup
from flask.cli import with_appcontext

config_cli = AppGroup("config", help="Manage configuration.")


@config_cli.command("show")
@with_appcontext
def show_config():
    """Show the current configuration."""
    click.echo(yaml.dump(dict(app.config)))

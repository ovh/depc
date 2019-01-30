import yaml
from flask_script import Command


class GetConfig(Command):
    """Gives information about the configuration file used."""

    def __init__(self, app):
        self.app = app

    def run(self):
        print(yaml.dump(dict(self.app.config)))

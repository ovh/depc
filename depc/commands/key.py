from flask import current_app as app
from flask_script import Command, Option, Manager

from depc.extensions.encrypted_dict import FlaskEncryptedDict


class ChangeKey(Command):

    option_list = (
        Option("--new-key", type=str, default=None),
        Option("--old-key", type=str, default=None),
    )

    def run(self, new_key, old_key):
        if not old_key:
            old_key = app.config.get("DB_ENCRYPTION_KEY", None)

        FlaskEncryptedDict.change_key(old_key, new_key)
        print("Database key has been changed")
        print("Add this key to depc.{env}.yml as DB_ENCRYPTION_KEY")
        print(new_key)


class GenerateKey(Command):
    """Generate a 256 bits hex key to encrypt database"""

    def run(self):
        print(FlaskEncryptedDict.generate_key())


key_manager = Manager(app)
key_manager.__doc__ = "Manager database key"
key_manager.add_command("change-key", ChangeKey)
key_manager.add_command("generate-key", GenerateKey)

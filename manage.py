import os

from depc import create_app
from depc.commands.config import config_cli
from depc.commands.key import key_cli

env = os.getenv("DEPC_ENV", "dev")

app = create_app(environment=env)
app.cli.add_command(config_cli)
app.cli.add_command(key_cli)


if __name__ == "__main__":
    app.run(debug=(env == "dev"))

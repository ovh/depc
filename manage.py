import os

from flask_script import Shell, Manager
from flask_script.commands import ShowUrls
from flask_migrate import MigrateCommand

from depc import create_app
from depc.commands.getconfig import GetConfig
from depc.commands.key import key_manager


# Create an application using the `api` context
app = create_app(
    environment=os.getenv('DEPC_ENV') or 'dev',
)
manager = Manager(app)


@manager.shell
def make_shell_context():
    return dict(app=app)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('getconfig', GetConfig(app))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls)
manager.add_command('key', key_manager)

if __name__ == '__main__':
    manager.run()

from flask_admin import Admin
from flask_admin.base import AdminIndexView
from flask_cors import CORS
from flask_jsonschema import JsonSchema
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event, exc, select
from sqlalchemy.engine import Engine

from depc.extensions.encrypted_dict import FlaskEncryptedDict
from depc.extensions.flask_redis_cache import FlaskRedisCache

admin = Admin(index_view=AdminIndexView())
db = SQLAlchemy(session_options={"autoflush": False})
migrate = Migrate()
cors = CORS(send_wildcard=True)
jsonschema = JsonSchema()
flask_encrypted_dict = FlaskEncryptedDict()
login_manager = LoginManager()
redis = FlaskRedisCache()
redis_scheduler = FlaskRedisCache()


@login_manager.request_loader
def load_user_from_request(request):
    from depc.models.users import User

    username = request.headers.get("X-Remote-User")
    if not username:
        return None

    # Create the user if it not yet exists
    user = User.query.filter_by(name=username).first()
    if not user:
        user = User(name=username)
        db.session.add(user)
        db.session.commit()

    return user


@event.listens_for(Engine, "engine_connect")
def ping_connection(connection, branch):
    # From http://docs.sqlalchemy.org/en/latest/core/pooling.html
    if branch or connection.should_close_with_result:
        # "branch" refers to a sub-connection of a connection,
        # "should_close_with_result" close request after result
        # we don't want to bother pinging on these.
        return

    try:
        # run a SELECT 1.   use a core select() so that
        # the SELECT of a scalar value without a table is
        # appropriately formatted for the backend
        connection.scalar(select([1]))
    except exc.DBAPIError as err:
        # catch SQLAlchemy's DBAPIError, which is a wrapper
        # for the DBAPI's exception.  It includes a .connection_invalidated
        # attribute which specifies if this connection is a "disconnect"
        # condition, which is based on inspection of the original exception
        # by the dialect in use.
        if err.connection_invalidated:
            # run the same SELECT again - the connection will re-validate
            # itself and establish a new connection.  The disconnect detection
            # here also causes the whole connection pool to be invalidated
            # so that all stale connections are discarded.
            connection.scalar(select([1]))
        else:
            raise

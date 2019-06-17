import json
import os
import tempfile
from pathlib import Path

import pytest
from deepdiff import DeepDiff
from flask import Response
from flask.testing import FlaskClient
from neo4j.exceptions import AuthError, ServiceUnavailable
from werkzeug.datastructures import Headers

from depc import create_app
from depc.controllers.checks import CheckController
from depc.controllers.configs import ConfigController
from depc.controllers.grants import GrantController
from depc.controllers.rules import RuleController
from depc.controllers.sources import SourceController
from depc.controllers.teams import TeamController
from depc.controllers.users import UserController
from depc.controllers.news import NewsController
from depc.extensions import db
from depc.utils.neo4j import get_records, set_records


class DepcTestClient(FlaskClient):
    def __init__(self, *args, **kwargs):
        self._login = None
        super(DepcTestClient, self).__init__(*args, **kwargs)

    def login(self, login):
        self._login = login

    def logout(self):
        self._login = None

    def open(self, *args, **kwargs):
        headers = kwargs.pop('headers', Headers())

        if self._login:
            headers.extend({'X-Remote-User': self._login})
            kwargs['headers'] = headers
        return super().open(*args, **kwargs)


class DepcResponse(Response):

    KEYS_TO_REMOVE = [
        'id',
        'createdAt',
        'updatedAt',
        'created_at',
        'updated_at'
    ]

    def remove_keys(self, d, keys):
        if isinstance(keys, str):
            keys = [keys]
        if isinstance(d, dict):
            for key in set(keys):
                if key in d:
                    del d[key]
            for k, v in d.items():
                self.remove_keys(v, keys)
        elif isinstance(d, list):
            for i in d:
                self.remove_keys(i, keys)
        return d

    @property
    def json(self):
        data = json.loads(self.data.decode('utf-8'))
        self.remove_keys(data, self.KEYS_TO_REMOVE)
        return data

    def raises_required_property(self, prop):
        wanted = {'message': "'{}' is a required property".format(prop)}
        return self.status_code == 400 and self.json == wanted


@pytest.fixture(scope='module')
def app_module():
    db_fd = db_path = None
    app = create_app(
        environment='test',
    )

    # Choose tests database
    if app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite://':
        db_fd, db_path = tempfile.mkstemp()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}.db'.format(db_path)

    with app.app_context():
        db.create_all()

    app.response_class = DepcResponse
    app.test_client_class = DepcTestClient
    yield app

    with app.app_context():
        db.drop_all()

    if db_fd and db_path:
        os.close(db_fd)
        os.unlink(db_path)

    return app_module


@pytest.fixture(scope='function')
def app(app_module):
    """This code is called between each test."""
    with app_module.app_context():

        # Clean the relational database
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

    return app_module


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def skip_by_requirement(app, request):
    """Skip a test if the requirement is not met.

    Supporting argument: "neo4j"

    Usage:

        >>> @pytest.mark.skip_requirement('neo4j')
        >>> def test_get_team_dependencies(client):
        >>>    pass
    """
    if request.node.get_closest_marker('skip_requirement'):

        # Skip test if neo4j is not running (or not well configured)
        if request.node.get_closest_marker('skip_requirement').args[0] == 'neo4j':
            with app.app_context():
                try:
                    get_records("RETURN 1")
                except ServiceUnavailable as e:
                    pytest.skip("Neo4j server error : {}".format(e))
                except AuthError as e:
                    pytest.skip("Neo4j authentication error : {}".format(e))


@pytest.fixture
def create_team(app):
    def _create_team(name, metas={}):
        data = {"name": name}
        if metas:
            data["metas"] = metas
        with app.app_context():
            return TeamController.create(data)
    return _create_team


@pytest.fixture
def create_user(app):
    def _create_user(name):
        with app.app_context():
            return UserController.create({
                'name': name
            })
    return _create_user


@pytest.fixture
def create_grant(app):
    def _create_grant(team_id, user_id, role='member'):
        with app.app_context():
            return GrantController.create({
                'team_id': team_id,
                'user_id': user_id,
                'role': role
            })
    return _create_grant


@pytest.fixture
def create_source(app):
    def _create_source(name, team_id, plugin='Fake', conf={}):
        with app.app_context():
            return SourceController.create({
                'team_id': team_id,
                'name': name,
                'plugin': plugin,
                'configuration': conf
            })
    return _create_source


@pytest.fixture
def create_rule(app):
    def _create_rule(name, team_id, description=None):
        with app.app_context():
            return RuleController.create({
                'team_id': team_id,
                'name': name,
                'description': description
            })
    return _create_rule


@pytest.fixture
def create_check(app):
    def _create_check(name, source_id, type='Threshold', parameters={}):
        with app.app_context():
            return CheckController.create({
                'source_id': source_id,
                'name': name,
                'type': type,
                'parameters': parameters
            })
    return _create_check


@pytest.fixture
def add_check(app):
    def _add_check(rule_id, checks_id):
        with app.app_context():
            return RuleController.update_checks(
                rule_id=rule_id,
                checks_id=checks_id
            )
    return _add_check


@pytest.fixture
def create_config(app):
    def _create_config(team_id, conf={}):
        with app.app_context():
            return ConfigController.create({
                'team_id': team_id,
                'data': conf
            })
    return _create_config


@pytest.fixture
def create_news(app):
    def _create_news(title, message=None, users=[]):
        with app.app_context():
            news = NewsController._create({
                'title': title,
                'message': message
            })

            if users:
                news.users = users
                db.session.add(news)
                db.session.commit()

            return NewsController.resource_to_dict(news)
    return _create_news


@pytest.fixture
def open_mock():
    def _open_mock(name):
        path = Path(__file__).resolve().parent / 'data/{}.json'.format(name)
        with path.open() as f:
            data = json.load(f)
        return data
    return _open_mock


@pytest.fixture
def is_mock_equal(open_mock):
    def _is_mock_equal(data, mock_name):
        mock = open_mock(mock_name)
        return DeepDiff(data, mock, ignore_order=True) == {}
    return _is_mock_equal


@pytest.fixture(scope='function')
def neo(app_module):
    """This code is called between each test."""
    with app_module.app_context():

        # Clean the Neo4j database
        set_records("MATCH (n) DETACH DELETE n;")

    return app_module


@pytest.fixture
def neo_create(app, neo):
    def _neo_create(query):
        with app.app_context():
            return set_records(query)
    return _neo_create

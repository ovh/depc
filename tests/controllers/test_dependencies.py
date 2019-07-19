import pytest

from depc.controllers.dependencies import DependenciesController


def test_build_dependencies_query_without_config(app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Server',
            node='server.ovh.net',
            filter_on_config=False
        )
    assert query == ("MATCH(n:acme_Server{name: 'server.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


def test_build_dependencies_query_rule(app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'Server': {'qos': 'rule.Servers'}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Server',
            node='server.ovh.net',
            filter_on_config=True
        )
    assert query == ("MATCH(n:acme_Server{name: 'server.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


def test_build_dependencies_query_with_impacted_nodes(app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'Server': {'qos': 'rule.Servers'}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Server',
            node='server.ovh.net',
            filter_on_config=True,
            impacted=True
        )
    assert query == ("MATCH(n:acme_Server{name: 'server.ovh.net'}) "
                     "OPTIONAL MATCH (n)<-[r]-(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


@pytest.mark.parametrize("method", [("operation"), ("aggregation")])
def test_build_dependencies_query_one_dep(method, app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'Server': {'qos': 'rule.Servers'},
        'Cluster': {'qos': '{0}.AND[Server]'.format(method)}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Cluster',
            node='cluster.ovh.net',
            filter_on_config=True
        )
    assert query == ("MATCH(n:acme_Cluster{name: 'cluster.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "WHERE 'acme_Server' IN LABELS(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


@pytest.mark.parametrize("method", [("operation"), ("aggregation")])
def test_build_dependencies_query_multiple_deps(method, app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'ServerA': {'qos': 'rule.Servers'},
        'ServerB': {'qos': 'rule.Servers'},
        'Cluster': {'qos': '{0}.AND[ServerA, ServerB]'.format(method)}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Cluster',
            node='cluster.ovh.net',
            filter_on_config=True
        )
    assert query == ("MATCH(n:acme_Cluster{name: 'cluster.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "WHERE 'acme_ServerA' IN LABELS(m) "
                     "OR 'acme_ServerB' IN LABELS(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


def test_build_query_count_nodes(app):
    with app.app_context():
        query = DependenciesController()._build_query_count_nodes(
            topic='acme',
            labels=['Foo']
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH 'Foo' AS Label, count(n) AS Count "
        "RETURN Label, Count "
    )

    with app.app_context():
        query = DependenciesController()._build_query_count_nodes(
            topic='acme',
            labels=['Foo', 'Bar', 'Baz']
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH 'Foo' AS Label, count(n) AS Count "
        "RETURN Label, Count "
        "UNION MATCH (n:acme_Bar) WITH 'Bar' AS Label, count(n) AS Count "
        "RETURN Label, Count "
        "UNION MATCH (n:acme_Baz) WITH 'Baz' AS Label, count(n) AS Count "
        "RETURN Label, Count "
    )


def test_build_query_nodes(app):
    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo'
        )
    assert query == "MATCH (n:acme_Foo) WITH n RETURN n.name"

    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo',
            random=True
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH n"
        ", rand() as r ORDER BY r "
        "RETURN n.name"
    )

    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo',
            random=True,
            name="bar"
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH n"
        ", rand() as r ORDER BY r "
        "WHERE n.name CONTAINS 'bar' "
        "RETURN n.name"
    )

    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo',
            random=True,
            name="bar",
            limit=1234
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH n"
        ", rand() as r ORDER BY r "
        "WHERE n.name CONTAINS 'bar' "
        "RETURN n.name "
        "LIMIT 1234"
    )

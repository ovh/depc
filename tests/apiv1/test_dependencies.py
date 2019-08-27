import json
from unittest.mock import PropertyMock, patch

import arrow
import pytest

# Skip these tests if no instance of neo4j is available
pytestmark = pytest.mark.skip_requirement('neo4j')


def test_get_labels_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/labels'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/labels'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/labels'.format(team_id))
        assert resp.status_code == 200


def test_get_labels_notfound(client):
    client.login('depc')

    resp = client.get('/v1/teams/notfound/labels')
    assert resp.status_code == 404


def test_get_labels(app, client, create_team, create_user, create_grant, create_rule, create_config, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/{}/labels'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == []

    neo_create("CREATE (main:acme_MyLabel{name: 'first'})")
    resp = client.get('/v1/teams/{}/labels'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == [{'name': 'MyLabel', 'nodes_count': 1, 'qos_query': None}]

    create_rule('MyRule', team_id)
    create_config(team_id, {'MyLabel': {'qos': 'rule.MyRule'}})
    neo_create("CREATE (main:acme_MyLabel{name: 'first'})")
    resp = client.get('/v1/teams/{}/labels'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == [{'name': 'MyLabel', 'nodes_count': 2, 'qos_query': 'rule.MyRule'}]

    neo_create("MATCH (n:acme_MyLabel) DELETE n")
    resp = client.get('/v1/teams/{}/labels'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == [{'name': 'MyLabel', 'nodes_count': 0, 'qos_query': 'rule.MyRule'}]


def test_get_label_nodes_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/labels/MyLabel/nodes'.format(team_id))
        assert resp.status_code == 200


def test_get_label_nodes_notfound(client):
    client.login('depc')
    resp = client.get('/v1/teams/notfound/labels/MyLabel/nodes')
    assert resp.status_code == 404


def test_get_label_nodes(client, create_team, create_user, create_grant, neo_create):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('Acme')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == []

    neo_create("CREATE (n:acme_MyLabel{name: 'node0'})")
    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == ['node0']

    nodes = ['node{}'.format(i) for i in range(1, 11)]
    for node in nodes:
        neo_create("CREATE (n:acme_MyLabel{name: '" + node + "'})")
    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes'.format(team_id))
    assert resp.status_code == 200
    assert sorted(resp.json) == sorted(['node0'] + nodes)

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes?name=node1'.format(team_id))
    assert resp.status_code == 200
    assert len(resp.json) == 2
    assert sorted(resp.json) == ['node1', 'node10']

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes?limit=5'.format(team_id))
    assert resp.status_code == 200
    assert len(resp.json) == 5

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes?random=true'.format(team_id))
    assert resp.status_code == 200
    assert len(resp.json) == 11


def test_count_node_dependencies_authorization(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes/foo/count'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes/foo/count'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/labels/MyLabel/nodes/foo/count'.format(team_id))
        assert resp.status_code == 200


def test_count_node_dependencies_notfound(client, create_team, create_user, create_grant):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/notfound/labels/MyLabel/nodes/foo/count')
    assert resp.status_code == 404

    resp = client.get('/v1/teams/{}/labels/LabelNotExists/nodes/NodeNotExists/count'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {'count': 0}


@pytest.mark.parametrize("number", [0, 1, 10])
def test_count_node_dependencies(number, app, client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # Build the query depending the number of wanted dependencies
    query = "CREATE (main:acme_MyLabel{name: 'main'}) "
    for i in range(number):
        query += ", (n" + str(i) + ":acme_MyLabel{name: 'n" + str(i) + "'}) "

    for i in range(number):
        query += "MERGE (main)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(n" + str(i) + ") "
    neo_create(query)

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes/main/count'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {'count': number}


def test_get_node_dependencies_authorization(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    neo_create("CREATE (n:acme_Cluster{name: 'cluster01'})")

    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
        assert resp.status_code == 200


def test_get_node_dependencies_notfound(client):
    client.login('depc')
    resp = client.get('/v1/teams/notfound/labels/MyLabel/nodes/foo')
    assert resp.status_code == 404


def test_get_node_alone(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes/cluster01'.format(team_id))
    assert resp.status_code == 404
    assert resp.json == {'message': 'Node cluster01 does not exist'}

    neo_create("CREATE (n:acme_Cluster{name: 'cluster01'})")
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01?alone=1'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {'name': 'cluster01'}
    assert "dependencies" not in resp.json
    assert "graph" not in resp.json


def test_get_node_dependencies_basic(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    resp = client.get('/v1/teams/{}/labels/MyLabel/nodes/cluster01'.format(team_id))
    assert resp.status_code == 404
    assert resp.json == {'message': 'Node cluster01 does not exist'}

    neo_create("CREATE (n:acme_Cluster{name: 'cluster01'})")
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.json['name'] == 'cluster01'
    assert resp.json['dependencies'] == {'Cluster': [{'name': 'cluster01'}]}
    assert resp.json['graph'] == {
        'nodes': [{'label': 'cluster01', 'title': 'Cluster'}],
        'relationships': []
    }

    # With one dependency
    neo_create(
        "MATCH (c:acme_Cluster{name: 'cluster01'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(s:acme_Server{name: 'server001'})"
    )
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [{'name': 'server001', 'inactive': False, 'periods': [0]}]
    }

    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['server001'], 'label': 'server001', 'title': 'Server'}
    ]

    assert len(rels) == 1
    assert rels == [{
        'id': rels[0]['id'], 'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server001'], 'periods': [0]
    }]

    # With two dependencies
    neo_create(
        "MATCH (c:acme_Cluster{name: 'cluster01'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(s:acme_Server{name: 'server002'})"
    )
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [
            {'name': 'server001', 'inactive': False, 'periods': [0]},
            {'name': 'server002', 'inactive': False, 'periods': [0]}
        ]
    }

    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['server001'], 'label': 'server001', 'title': 'Server'},
        {'id': ids['server002'], 'label': 'server002', 'title': 'Server'}
    ]

    assert len(rels) == 2
    for r in rels:
        del r['id']
    assert rels == [
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server001'], 'periods': [0]},
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server002'], 'periods': [0]}
    ]


def test_get_node_dependencies_selecting_day(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # server002 periods :
    #   - from 0
    #   - to 1549022400 (Friday 1 February 2019 12:00:00)
    #   - from 1550232000 (Friday 15 February 2019 12:00:00)
    neo_create(
        "CREATE (c:acme_Cluster{name: 'cluster01'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(s1:acme_Server{name: 'server001'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 1550232000, periods: [0,1549022400, 1550232000]}]->(s2:acme_Server{name: 'server002'})"
    )

    # Now is fixed the 2019-02-05, when only server001 was active
    fixed_now = arrow.get(2019, 2, 5)
    with patch('depc.apiv1.dependencies.arrow.utcnow', return_value=fixed_now):
        resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))

    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [
            {'name': 'server001', 'inactive': False, 'periods': [0]}
        ]
    }

    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['server001'], 'label': 'server001', 'title': 'Server'}
    ]

    assert len(rels) == 1
    for r in rels:
        del r['id']
    assert rels == [
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server001'], 'periods': [0]}
    ]

    # 2019-01-01 : the two dependencies are active
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01?day=2019-01-01'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [
            {'name': 'server001', 'inactive': False, 'periods': [0]},
            {'name': 'server002', 'inactive': False, 'periods': [0, 1549022400, 1550232000]}
        ]
    }
    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['server001'], 'label': 'server001', 'title': 'Server'},
        {'id': ids['server002'], 'label': 'server002', 'title': 'Server'},
    ]

    assert len(rels) == 2
    for r in rels:
        del r['id']
    assert rels == [
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server001'], 'periods': [0]},
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server002'], 'periods': [0, 1549022400, 1550232000]}
    ]

    # 2019-02-10 : server002 is inactive
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01?day=2019-02-10'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [
            {'name': 'server001', 'inactive': False, 'periods': [0]}
        ]
    }

    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['server001'], 'label': 'server001', 'title': 'Server'}
    ]

    assert len(rels) == 1
    for r in rels:
        del r['id']
    assert rels == [
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server001'], 'periods': [0]}
    ]


def test_get_node_dependencies_with_inactives(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # server002 periods :
    #   - from 0
    #   - to 1549022400 (Friday 1 February 2019 12:00:00)
    neo_create(
        "CREATE (c:acme_Cluster{name: 'cluster01'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(s1:acme_Server{name: 'server001'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'to', last_ts: 1549022400, periods: [0, 1549022400]}]->(s2:acme_Server{name: 'server002'})"
    )

    # Now is fixed the 2019-02-05, when only server001 was active
    fixed_now = arrow.get(2019, 2, 5)
    with patch('depc.apiv1.dependencies.arrow.utcnow', return_value=fixed_now):
        resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01?inactive=1'.format(team_id))

    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [
            {'name': 'server001', 'inactive': False, 'periods': [0]},
            {'name': 'server002', 'inactive': True, 'periods': [0, 1549022400]}
        ]
    }

    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['server001'], 'label': 'server001', 'title': 'Server'},
        {'id': ids['server002'], 'label': 'server002', 'title': 'Server'}
    ]

    assert len(rels) == 2
    for r in rels:
        del r['id']
    assert rels == [
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server001'], 'periods': [0]},
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['server002'], 'periods': [0, 1549022400]}
    ]


def test_get_node_dependencies_with_config(client, create_team, create_user, create_grant, create_rule, create_config, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    create_rule('MyServerRule', team_id)
    create_rule('MyClusterRule', team_id)
    create_config(team_id, {
        'Cluster': {'qos': 'operation.AND[ServerA]'},
        'ServerA': {'qos': 'rule.MyServerRule'}
    })
    neo_create(
        "CREATE (c:acme_Cluster{name: 'cluster01'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(sa:acme_ServerA{name: 'serverA'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(sb:acme_ServerB{name: 'serverB'}) "
    )

    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01?config=1'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'ServerA': [
            {'name': 'serverA', 'inactive': False, 'periods': [0]}
        ]
    }
    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field

        nodes = resp.json['graph']['nodes']
        rels = resp.json['graph']['relationships']

    ids = {n['label']: n['id'] for n in nodes}
    assert nodes == [
        {'id': ids['cluster01'], 'label': 'cluster01', 'title': 'Cluster'},
        {'id': ids['serverA'], 'label': 'serverA', 'title': 'ServerA'}
    ]

    assert len(rels) == 1
    for r in rels:
        del r['id']
    assert rels == [
        {'arrows': 'to', 'from': ids['cluster01'], 'to': ids['serverA'], 'periods': [0]}
    ]


def test_get_node_dependencies_with_impacted_nodes(client, create_team, create_user, create_grant, create_rule, create_config, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # One node with two dependencies
    neo_create(
        "CREATE (c:acme_Cluster{name: 'cluster01'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(s1:acme_Server{name: 'server001'}) "
        "MERGE (c)-[:DEPENDS_ON{last_state: 'from', last_ts: 0, periods: [0]}]->(s2:acme_Server{name: 'server002'})"
    )

    # Display upstream nodes
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}],
        'Server': [
            {'name': 'server001', 'inactive': False, 'periods': [0]},
            {'name': 'server002', 'inactive': False, 'periods': [0]}
        ]
    }

    resp = client.get('/v1/teams/{}/labels/Server/nodes/server001'.format(team_id))
    assert resp.json['dependencies'] == {
        'Server': [{'name': 'server001'}]
    }

    # Display impacted nodes
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes/cluster01?impacted=1'.format(team_id))
    assert resp.json['dependencies'] == {
        'Cluster': [{'name': 'cluster01'}]
    }

    resp = client.get('/v1/teams/{}/labels/Server/nodes/server001?impacted=1'.format(team_id))
    assert resp.json['dependencies'] == {
        'Server': [{'name': 'server001'}],
        'Cluster': [{'inactive': False, 'name': 'cluster01', 'periods': [0]}]
    }


def test_delete_node_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.delete('/v1/teams/{}/labels/MyLabel/nodes/foo'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.delete('/v1/teams/{}/labels/MyLabel/nodes/foo'.format(team_id))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 403, 'manager': 200}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.delete('/v1/teams/{}/labels/MyLabel/nodes/foo'.format(team_id))
        assert resp.status_code == status


def test_delete_node_notfound(client):
    client.login('depc')
    resp = client.delete('/v1/teams/notfound/labels/MyLabel/nodes/foo')
    assert resp.status_code == 404


def test_delete_node(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('depc')

    neo_create("CREATE (c:acme_Cluster{name: 'cluster01'})")
    resp = client.get('/v1/teams/{}/labels/Cluster/nodes'.format(team_id))
    assert resp.json == ['cluster01']

    resp = client.delete('/v1/teams/{}/labels/Cluster/nodes/cluster01'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {}

    resp = client.get('/v1/teams/{}/labels/Cluster/nodes'.format(team_id))
    assert resp.json == []


def test_get_impacted_nodes(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # Create the following nodes with the following relationships
    # (from/to/periods not indicated to improve readability)
    #
    #                                    DEPENDS_ON
    #                                 ||===========> (ftp02)
    #                DEPENDS_ON       ||
    #             ||===========> (website03) ==||
    #             ||                           ||
    #             ||                           || DEPENDS_ON              DEPENDS_ON             DEPENDS_ON
    # (offer01) ==||===========> (website01) ==||===========> (server02) ===========> (other-A) ===========> (other-B)
    #             ||                           ||                                                               ||
    #             ||                           ||                             DEPENDS_ON             DEPENDS_ON ||
    #             ||===========> (website02) ==||                  (other-D) <=========== (other-C) <===========||
    #             ||
    #             ||                          DEPENDS_ON
    #             ||===========> (web-other) ===========> (ftp01)
    #                                ||
    #                                || DEPENDS_ON
    #                                ||===========> (server01)
    neo_create(
        "MERGE(off1:acme_Offer{name:'offer01', from: 1566338400}) "
        "MERGE(web1:acme_Website{name:'website01', from: 1566424800}) "
        "MERGE(web3:acme_Website{name:'website03', from: 1566079200}) "
        "MERGE(web2:acme_Website{name:'website02', from: 1566079200}) "
        "MERGE(web_other:acme_Website{name:'web-other', from: 1566338400}) "
        "MERGE(serv1:acme_Server{name:'server01', from: 1566338400}) "
        "MERGE(serv2:acme_Server{name:'server02', from: 1566079200}) "
        "MERGE(ftp1:acme_Ftp{name:'ftp01', from: 1566338400}) "
        "MERGE(ftp2:acme_Ftp{name:'ftp02', from: 1566338400}) "
        "MERGE(other_a:acme_OtherA{name:'other-A', from: 1566338400}) "
        "MERGE(other_b:acme_OtherB{name:'other-B', from: 1566165600, to: 1566252000}) "
        "MERGE(other_c:acme_OtherC{name:'other-C', from: 1566338400}) "
        "MERGE(other_d:acme_OtherD{name:'other-D', from: 1566338400}) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566338400]}]->(web1) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(web3) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(web2) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566338400]}]->(web_other) "
        "MERGE(web_other)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(serv1) "
        "MERGE(web_other)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(ftp1) "
        "MERGE(web1)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(serv2) "
        "MERGE(web3)-[:DEPENDS_ON{periods: [1566338400]}]->(serv2) "
        "MERGE(web3)-[:DEPENDS_ON{periods: [1566338400]}]->(ftp2) "
        "MERGE(web2)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(serv2) "
        "MERGE(serv2)-[:DEPENDS_ON{periods: [1566338400]}]->(other_a) "
        "MERGE(other_a)-[:DEPENDS_ON{periods: [1566338400]}]->(other_b) "
        "MERGE(other_b)-[:DEPENDS_ON{periods: [1566338400]}]->(other_c) "
        "MERGE(other_c)-[:DEPENDS_ON{periods: [1566338400]}]->(other_d)"
    )

    # Display which acme_Website nodes are impacted by the server02 node at timestamp 1566424800
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted'
        '?1=1&impactedLabel=Website&skip=0&limit=25&ts=1566424800'.format(team_id)
    )
    assert resp.json == [
        {
            "active": True,
            "from": 1566424800,
            "name": "website01",
            "to": None
        },
        {
            "active": False,
            "from": 1566079200,
            "name": "website02",
            "to": None
        },
        {
            "active": True,
            "from": 1566079200,
            "name": "website03",
            "to": None
        }
    ]

    # Display which acme_Website nodes are impacted by the server02 node at timestamp 1566338400
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted'
        '?1=1&impactedLabel=Website&skip=0&limit=25&ts=1566338400'.format(team_id)
    )
    assert resp.json == [
        {
            "active": False,
            "from": 1566424800,
            "name": "website01",
            "to": None
        },
        {
            "active": False,
            "from": 1566079200,
            "name": "website02",
            "to": None
        },
        {
            "active": True,
            "from": 1566079200,
            "name": "website03",
            "to": None
        }
    ]

    # Display which acme_Website nodes are impacted by the server02 node at timestamp 1566252000
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted'
        '?1=1&impactedLabel=Website&skip=0&limit=25&ts=1566252000'.format(team_id)
    )
    assert resp.json == [
        {
            "active": False,
            "from": 1566424800,
            "name": "website01",
            "to": None
        },
        {
            "active": True,
            "from": 1566079200,
            "name": "website02",
            "to": None
        },
        {
            "active": False,
            "from": 1566079200,
            "name": "website03",
            "to": None
        }
    ]

    # Display which acme_Website nodes are impacted by the server02 node at timestamp 1566079200
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted'
        '?1=1&impactedLabel=Website&skip=0&limit=25&ts=1566079200'.format(team_id)
    )
    assert resp.json == [
        {
            "active": False,
            "from": 1566424800,
            "name": "website01",
            "to": None
        },
        {
            "active": False,
            "from": 1566079200,
            "name": "website02",
            "to": None
        },
        {
            "active": False,
            "from": 1566079200,
            "name": "website03",
            "to": None
        }
    ]

    # Display which acme_Offer nodes are impacted by the server02 node at timestamp 1566424800
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted'
        '?1=1&impactedLabel=Offer&skip=0&limit=25&ts=1566424800'.format(team_id)
    )
    assert resp.json == [
        {
            "active": True,
            "from": 1566338400,
            "name": "offer01",
            "to": None
        }
    ]


def test_get_impacted_nodes_count(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # Create the following nodes with the following relationships
    # (from/to/periods not indicated to improve readability)
    #
    #                                    DEPENDS_ON
    #                                 ||===========> (ftp02)
    #                DEPENDS_ON       ||
    #             ||===========> (website03) ==||
    #             ||                           ||
    #             ||                           || DEPENDS_ON              DEPENDS_ON             DEPENDS_ON
    # (offer01) ==||===========> (website01) ==||===========> (server02) ===========> (other-A) ===========> (other-B)
    #             ||                           ||                                                               ||
    #             ||                           ||                             DEPENDS_ON             DEPENDS_ON ||
    #             ||===========> (website02) ==||                  (other-D) <=========== (other-C) <===========||
    #             ||
    #             ||                          DEPENDS_ON
    #             ||===========> (web-other) ===========> (ftp01)
    #                                ||
    #                                || DEPENDS_ON
    #                                ||===========> (server01)
    neo_create(
        "MERGE(off1:acme_Offer{name:'offer01', from: 1566338400}) "
        "MERGE(web1:acme_Website{name:'website01', from: 1566424800}) "
        "MERGE(web3:acme_Website{name:'website03', from: 1566079200}) "
        "MERGE(web2:acme_Website{name:'website02', from: 1566079200}) "
        "MERGE(web_other:acme_Website{name:'web-other', from: 1566338400}) "
        "MERGE(serv1:acme_Server{name:'server01', from: 1566338400}) "
        "MERGE(serv2:acme_Server{name:'server02', from: 1566079200}) "
        "MERGE(ftp1:acme_Ftp{name:'ftp01', from: 1566338400}) "
        "MERGE(ftp2:acme_Ftp{name:'ftp02', from: 1566338400}) "
        "MERGE(other_a:acme_OtherA{name:'other-A', from: 1566338400}) "
        "MERGE(other_b:acme_OtherB{name:'other-B', from: 1566165600, to: 1566252000}) "
        "MERGE(other_c:acme_OtherC{name:'other-C', from: 1566338400}) "
        "MERGE(other_d:acme_OtherD{name:'other-D', from: 1566338400}) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566338400]}]->(web1) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(web3) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(web2) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566338400]}]->(web_other) "
        "MERGE(web_other)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(serv1) "
        "MERGE(web_other)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(ftp1) "
        "MERGE(web1)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(serv2) "
        "MERGE(web3)-[:DEPENDS_ON{periods: [1566338400]}]->(serv2) "
        "MERGE(web3)-[:DEPENDS_ON{periods: [1566338400]}]->(ftp2) "
        "MERGE(web2)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(serv2) "
        "MERGE(serv2)-[:DEPENDS_ON{periods: [1566338400]}]->(other_a) "
        "MERGE(other_a)-[:DEPENDS_ON{periods: [1566338400]}]->(other_b) "
        "MERGE(other_b)-[:DEPENDS_ON{periods: [1566338400]}]->(other_c) "
        "MERGE(other_c)-[:DEPENDS_ON{periods: [1566338400]}]->(other_d)"
    )

    # Display the number of acme_Website impacted by the server02 node
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted/count?impactedLabel=Website'.format(team_id)
    )
    assert resp.json == {
        "count": 3
    }

    # Display the number of acme_Offer impacted by the server02 node
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted/count?impactedLabel=Offer'.format(team_id)
    )
    assert resp.json == {
        "count": 1
    }


def test_get_impacted_nodes_all(client, create_team, create_user, create_grant, neo_create):
    team_id = str(create_team('Acme')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')
    client.login('depc')

    # Create the following nodes with the following relationships
    # (from/to/periods not indicated to improve readability)
    #
    #                                    DEPENDS_ON
    #                                 ||===========> (ftp02)
    #                DEPENDS_ON       ||
    #             ||===========> (website03) ==||
    #             ||                           ||
    #             ||                           || DEPENDS_ON              DEPENDS_ON             DEPENDS_ON
    # (offer01) ==||===========> (website01) ==||===========> (server02) ===========> (other-A) ===========> (other-B)
    #             ||                           ||                                                               ||
    #             ||                           ||                             DEPENDS_ON             DEPENDS_ON ||
    #             ||===========> (website02) ==||                  (other-D) <=========== (other-C) <===========||
    #             ||
    #             ||                          DEPENDS_ON
    #             ||===========> (web-other) ===========> (ftp01)
    #                                ||
    #                                || DEPENDS_ON
    #                                ||===========> (server01)
    neo_create(
        "MERGE(off1:acme_Offer{name:'offer01', from: 1566338400}) "
        "MERGE(web1:acme_Website{name:'website01', from: 1566424800}) "
        "MERGE(web3:acme_Website{name:'website03', from: 1566079200}) "
        "MERGE(web2:acme_Website{name:'website02', from: 1566079200}) "
        "MERGE(web_other:acme_Website{name:'web-other', from: 1566338400}) "
        "MERGE(serv1:acme_Server{name:'server01', from: 1566338400}) "
        "MERGE(serv2:acme_Server{name:'server02', from: 1566079200}) "
        "MERGE(ftp1:acme_Ftp{name:'ftp01', from: 1566338400}) "
        "MERGE(ftp2:acme_Ftp{name:'ftp02', from: 1566338400}) "
        "MERGE(other_a:acme_OtherA{name:'other-A', from: 1566338400}) "
        "MERGE(other_b:acme_OtherB{name:'other-B', from: 1566165600, to: 1566252000}) "
        "MERGE(other_c:acme_OtherC{name:'other-C', from: 1566338400}) "
        "MERGE(other_d:acme_OtherD{name:'other-D', from: 1566338400}) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566338400]}]->(web1) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(web3) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(web2) "
        "MERGE(off1)-[:DEPENDS_ON{periods: [1566338400]}]->(web_other) "
        "MERGE(web_other)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(serv1) "
        "MERGE(web_other)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(ftp1) "
        "MERGE(web1)-[:DEPENDS_ON{periods: [1566165600, 1566252000, 1566338400]}]->(serv2) "
        "MERGE(web3)-[:DEPENDS_ON{periods: [1566338400]}]->(serv2) "
        "MERGE(web3)-[:DEPENDS_ON{periods: [1566338400]}]->(ftp2) "
        "MERGE(web2)-[:DEPENDS_ON{periods: [1566165600, 1566252000]}]->(serv2) "
        "MERGE(serv2)-[:DEPENDS_ON{periods: [1566338400]}]->(other_a) "
        "MERGE(other_a)-[:DEPENDS_ON{periods: [1566338400]}]->(other_b) "
        "MERGE(other_b)-[:DEPENDS_ON{periods: [1566338400]}]->(other_c) "
        "MERGE(other_c)-[:DEPENDS_ON{periods: [1566338400]}]->(other_d)"
    )

    # Display all acme_Website nodes impacted by the server02 node at timestamp 1566424800
    # (with inactive nodes included)
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted/all'
        '?1=1&impactedLabel=Website&ts=1566424800&withInactiveNodes=true'.format(team_id)
    )

    data_json = json.loads(resp.json["data"])

    assert data_json == [
        {
            "active": True,
            "from": 1566424800,
            "name": "website01",
            "to": None
        },
        {
            "active": False,
            "from": 1566079200,
            "name": "website02",
            "to": None
        },
        {
            "active": True,
            "from": 1566079200,
            "name": "website03",
            "to": None
        }
    ]

    # Display all acme_Website nodes impacted by the server02 node at timestamp 1566338400
    # (without inactive nodes included)
    resp = client.get(
        '/v1/teams/{}/labels/Server/nodes/server02/impacted/all'
        '?1=1&impactedLabel=Website&ts=1566424800&withInactiveNodes=false'.format(team_id)
    )

    data_json = json.loads(resp.json["data"])

    assert data_json == [
        {
            "active": True,
            "from": 1566424800,
            "name": "website01",
            "to": None
        },
        {
            "active": True,
            "from": 1566079200,
            "name": "website03",
            "to": None
        }
    ]

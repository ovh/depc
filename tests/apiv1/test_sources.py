import json


def test_list_available_sources_authorization(client):
    resp = client.get('/v1/sources')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/sources')
    assert resp.status_code == 200


def test_list_available_sources(client, is_mock_equal):
    client.login('depc')
    resp = client.get('/v1/sources')
    assert resp.status_code == 200

    assert 'sources' in resp.json
    assert is_mock_equal(resp.json, 'available_sources')


def test_get_source_info_authorization(client):
    resp = client.get('/v1/sources/OpenTSDB')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB')
    assert resp.status_code == 200


def test_get_source_notfound(client):
    client.login('depc')
    resp = client.get('/v1/sources/notfound')
    assert resp.status_code == 404


def test_get_source_info(client, is_mock_equal):
    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB')
    assert resp.status_code == 200
    assert is_mock_equal(resp.json, 'opentsdb_source')


def test_list_available_checks_authorization(client):
    resp = client.get('/v1/sources/OpenTSDB/checks')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB/checks')
    assert resp.status_code == 200


def test_list_available_checks(client, is_mock_equal):
    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB/checks')
    assert resp.status_code == 200
    assert is_mock_equal(resp.json, 'opentsdb_checks')


def test_check_info_authorization(client):
    resp = client.get('/v1/sources/OpenTSDB/checks/Threshold')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB/checks/Threshold')
    assert resp.status_code == 200


def test_check_info_notfound(client):
    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB/checks/notfound')
    assert resp.status_code == 404


def test_check_info(client, is_mock_equal):
    client.login('depc')
    resp = client.get('/v1/sources/OpenTSDB/checks/Threshold')
    assert resp.status_code == 200
    assert is_mock_equal(resp.json, 'opentsdb_threshold_check')


def test_list_sources_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/sources'.format(team_id))
        assert resp.status_code == 200


def test_list_sources_notfound(client):
    client.login('depc')
    resp = client.get('/v1/teams/notfound/sources')
    assert resp.status_code == 404


def test_list_sources(client, create_team, create_user, create_grant, create_source, create_check):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('My team')['id'])
    create_grant(team_id, user_id, 'member')

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {'sources': []}

    source_id = str(create_source('My source', team_id)['id'])
    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {
        'sources': [{
            'name': 'My source',
            'plugin': 'Fake',
            'checks': []
        }]
    }

    create_check('My check', source_id, 'Threshold', {'metric': 'foo', 'threshold': 100})
    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {
        'sources': [{
            'name': 'My source',
            'plugin': 'Fake',
            'checks': [{
                'name': 'My check',
                'type': 'Threshold',
                'source_id': source_id,
                'parameters': {'metric': 'foo', 'threshold': 100},
            }]
        }]
    }

    for i in range(9):
        create_source('Source {}'.format(i), team_id)
    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 200
    assert len(resp.json['sources']) == 10

    # Manager can see the configuration
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')
    resp = client.get('/v1/teams/{}/sources'.format(team_id))
    assert resp.status_code == 200
    assert 'configuration' in resp.json['sources'][0]


def test_get_source_authorization(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    resp = client.get('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/sources/{}'.format(team_id, source_id))
        assert resp.status_code == 200


def test_get_team_source_notfound(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources/notfound'.format(team_id))
    assert resp.status_code == 404


def test_get_source(client, create_team, create_source, create_user, create_grant, create_check):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('My team')['id'])
    create_grant(team_id, user_id, 'member')
    source_id = str(create_source('My source', team_id)['id'])

    client.login('depc')
    resp = client.get('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 200
    assert resp.json == {
        'name': 'My source',
        'plugin': 'Fake',
        'checks': []
    }

    create_check('My check', source_id, 'Threshold', {'metric': 'foo', 'threshold': 100})
    resp = client.get('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 200
    assert resp.json == {
        'name': 'My source',
        'plugin': 'Fake',
        'checks': [{
            'name': 'My check',
            'type': 'Threshold',
            'source_id': source_id,
            'parameters': {'metric': 'foo', 'threshold': 100}
        }]
    }

    # Manager can see the configuration
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')
    resp = client.get('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 200
    assert 'configuration' in resp.json


def test_post_source_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    post_data = {'name': 'My source', 'plugin': 'Fake', 'configuration': {}}

    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 403, 'manager': 201}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
        assert resp.status_code == status


def test_post_source_notfound(client):
    post_data = {'name': 'My source', 'plugin': 'Fake', 'configuration': {}}
    client.login('depc')
    resp = client.post('/v1/teams/notfound/sources', data=json.dumps(post_data))
    assert resp.status_code == 404


def test_post_source(client, create_team, create_user, create_grant):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('My team')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('depc')

    post_data = {'plugin': 'Fake', 'configuration': {}}
    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.raises_required_property('name')

    post_data = {'name': 'My source', 'configuration': {}}
    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.raises_required_property('plugin')

    post_data = {'name': 'My source', 'plugin': 'Fake'}
    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.raises_required_property('configuration')

    post_data = {'name': 'My source', 'plugin': 'Fake', 'configuration': {}, 'additional': 'property'}
    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 400
    assert 'Additional properties are not allowed' in resp.json['message']

    post_data = {'name': 'My source', 'plugin': 'Fake', 'configuration': {}}
    resp = client.post('/v1/teams/{}/sources'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 201
    assert resp.json == {
        'name': 'My source',
        'plugin': 'Fake',
        'configuration': {},
        'checks': []
    }


def test_put_source_authorization(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    resp = client.put('/v1/teams/{}/sources/{}'.format(team_id, source_id), data=json.dumps({}))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.put('/v1/teams/{}/sources/{}'.format(team_id, source_id), data=json.dumps({}))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 403, 'manager': 200}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.put('/v1/teams/{}/sources/{}'.format(team_id, source_id), data=json.dumps({}))
        assert resp.status_code == status


def test_put_source_notfound(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.put('/v1/teams/notfound/sources/{}'.format(source_id), data=json.dumps({}))
    assert resp.status_code == 404
    resp = client.put('/v1/teams/{}/sources/notfound'.format(team_id), data=json.dumps({}))
    assert resp.status_code == 404


def test_put_source(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.put('/v1/teams/{}/sources/{}'.format(team_id, source_id), data=json.dumps({'additional': 'property'}))
    assert resp.status_code == 400
    assert 'Additional properties are not allowed' in resp.json['message']

    resp = client.put('/v1/teams/{}/sources/{}'.format(team_id, source_id), data=json.dumps({'name': 'My edited source'}))
    assert resp.status_code == 200
    assert resp.json == {
        'checks': [],
        'configuration': {},
        'name': 'My edited source',
        'plugin': 'Fake'
    }


def test_delete_source_authorization(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])

    resp = client.delete('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.delete('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 403, 'manager': 200}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.delete('/v1/teams/{}/sources/{}'.format(team_id, source_id))
        assert resp.status_code == status


def test_delete_source_notfound(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.delete('/v1/teams/notfound/sources/{}'.format(source_id), data=json.dumps({}))
    assert resp.status_code == 404
    resp = client.put('/v1/teams/{}/sources/notfound'.format(team_id), data=json.dumps({}))
    assert resp.status_code == 404


def test_delete_source(client, create_team, create_source, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    source_id = str(create_source('My source', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.delete('/v1/teams/{}/sources/{}'.format(team_id, source_id))
    assert resp.status_code == 200
    assert resp.json == {}

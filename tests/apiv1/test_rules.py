import json
import pytest


def test_list_rules_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/rules'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/rules'.format(team_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/rules'.format(team_id))
        assert resp.status_code == 200


def test_list_rules_notfound(client):
    client.login('depc')
    resp = client.get('/v1/teams/notfound/rules')
    assert resp.status_code == 404


def test_list_rules(client, create_team, create_user, create_grant, create_rule, create_source, create_check, add_check):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('My team')['id'])
    create_grant(team_id, user_id, 'member')

    client.login('depc')
    resp = client.get('/v1/teams/{}/rules'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {'rules': []}

    rule_id = str(create_rule('My rule', team_id)['id'])
    resp = client.get('/v1/teams/{}/rules'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == {
        'rules': [{
            'name': 'My rule',
            'description': None,
            'checks': []
        }]
    }

    source_id = str(create_source('My source', team_id)['id'])
    check_id = str(create_check('My check', source_id, 'Threshold', {'metric': 'foo', 'threshold': "100"})['id'])
    add_check(rule_id, [check_id])
    resp = client.get('/v1/teams/{}/rules'.format(team_id))
    assert resp.status_code == 200
    assert resp.json == resp.json == {
        'rules': [{
            'name': 'My rule',
            'description': None,
            'checks': [{
                'name': 'My check',
                'parameters': {'metric': 'foo', 'threshold': "100"},
                'source_id': source_id,
                'type': 'Threshold'
            }]
        }]
    }

    for i in range(9):
        create_rule('Rule {}'.format(i), team_id)
    resp = client.get('/v1/teams/{}/rules'.format(team_id))
    assert resp.status_code == 200
    assert len(resp.json['rules']) == 10


def test_get_rule_authorization(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])

    resp = client.get('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 403

    for role in ['member', 'editor', 'manager']:
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
        assert resp.status_code == 200


def test_get_rule_notfound(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('depc')['id'])
    create_grant(team_id, user_id, 'member')

    client.login('depc')
    resp = client.get('/v1/teams/{}/rules/notfound'.format(team_id))
    assert resp.status_code == 404


def test_get_rule(client, create_team, create_rule, create_user, create_grant, create_source, create_check, add_check):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('My team')['id'])
    create_grant(team_id, user_id, 'member')
    rule_id = str(create_rule('My rule', team_id)['id'])

    client.login('depc')
    resp = client.get('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 200
    assert resp.json == {
        'name': 'My rule',
        'description': None,
        'checks': []
    }

    source_id = str(create_source('My source', team_id)['id'])
    check_id = str(create_check('My check', source_id, 'Threshold', {'metric': 'foo', 'threshold': "100"})['id'])
    add_check(rule_id, [check_id])
    resp = client.get('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 200
    assert resp.json == resp.json == {
        'name': 'My rule',
        'description': None,
        'checks': [{
            'name': 'My check',
            'parameters': {'metric': 'foo', 'threshold': "100"},
            'source_id': source_id,
            'type': 'Threshold'
        }]
    }


def test_post_rule_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    post_data = {'name': 'My rule'}

    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 201, 'manager': 201}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.post(
            '/v1/teams/{}/rules'.format(team_id),
            data=json.dumps({'name': 'My {} rule'.format(role)})
        )
        assert resp.status_code == status


def test_post_rule_notfound(client):
    client.login('depc')
    resp = client.post('/v1/teams/notfound/rules', data=json.dumps({'name': 'My rule'}))
    assert resp.status_code == 404


def test_post_rule(client, create_team, create_user, create_grant):
    user_id = str(create_user('depc')['id'])
    team_id = str(create_team('My team')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('depc')

    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps({}))
    assert resp.raises_required_property('name')

    post_data = {'name': 'My rule', 'additional': 'property'}
    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps(post_data))
    assert resp.status_code == 400
    assert 'Additional properties are not allowed' in resp.json['message']

    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps({'name': 'My rule'}))
    assert resp.status_code == 201
    assert resp.json == {
        'name': 'My rule',
        'description': None,
        'checks': []
    }

    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps({'name': 'My rule'}))
    assert resp.status_code == 409

    resp = client.post(
        '/v1/teams/{}/rules'.format(team_id),
        data=json.dumps({'name': 'My second rule', 'description': 'My description'})
    )
    assert resp.status_code == 201
    assert resp.json == {
        'name': 'My second rule',
        'description': 'My description',
        'checks': []
    }


def test_put_rule_authorization(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])

    resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({}))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({}))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 200, 'manager': 200}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({}))
        assert resp.status_code == status


def test_put_rule_notfound(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.put('/v1/teams/notfound/rules/{}'.format(rule_id), data=json.dumps({}))
    assert resp.status_code == 404
    resp = client.put('/v1/teams/{}/rules/notfound'.format(team_id), data=json.dumps({}))
    assert resp.status_code == 404


def test_put_rule(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({'additional': 'property'}))
    assert resp.status_code == 400
    assert 'Additional properties are not allowed' in resp.json['message']

    resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({'name': 'My edited rule'}))
    assert resp.status_code == 200
    assert resp.json == {
        'checks': [],
        'name': 'My edited rule',
        'description': None
    }


def test_put_rule_with_config(client, create_team, create_rule, create_user, create_grant, create_config):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('MyRule', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    create_config(team_id, {'myLabel': {'qos': 'rule.MyRule'}})
    client.login('manager')

    resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({'name': 'My edited rule'}))
    assert resp.status_code == 409
    assert resp.json == {
        'message': 'Rule MyRule is used in your configuration, please remove it before.'
    }


def test_delete_rule_authorization(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])

    resp = client.delete('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.delete('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 403

    roles = {'member': 403, 'editor': 200, 'manager': 200}
    for role, status in roles.items():
        rule_id = str(create_rule('My {} rule'.format(role), team_id)['id'])
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.delete('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
        assert resp.status_code == status


def test_delete_rule_notfound(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.delete('/v1/teams/notfound/rules/{}'.format(rule_id), data=json.dumps({}))
    assert resp.status_code == 404
    resp = client.put('/v1/teams/{}/rule/notfound'.format(team_id), data=json.dumps({}))
    assert resp.status_code == 404


def test_delete_rule(client, create_team, create_rule, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.delete('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 200
    assert resp.json == {}


def test_delete_rule_with_config(client, create_team, create_rule, create_user, create_grant, create_config):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('MyRule', team_id)['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    create_config(team_id, {'myLabel': {'qos': 'rule.MyRule'}})
    client.login('manager')

    resp = client.delete('/v1/teams/{}/rules/{}'.format(team_id, rule_id))
    assert resp.status_code == 409
    assert resp.json == {
        'message': 'Rule MyRule is used in your configuration, please remove it before.'
    }


@pytest.mark.parametrize("test_input", ["'Test", "Test'", "'Test'", '"Test', 'Test"', '"Test"'])
def test_post_rule_prohibited_quotes(client, create_team, create_user, create_grant, test_input):
    team_id = str(create_team('My team')['id'])

    role = 'editor'
    user_id = str(create_user(role)['id'])
    create_grant(team_id, user_id, role)
    client.login(role)

    resp = client.post('/v1/teams/{}/rules'.format(team_id), data=json.dumps({'name': test_input}))
    assert resp.status_code == 400


@pytest.mark.parametrize("test_input", ["'Test", "Test'", "'Test'", '"Test', 'Test"', '"Test"'])
def test_put_rule_prohibited_quotes(client, create_team, create_user, create_grant, create_rule, test_input):
    team_id = str(create_team('My team')['id'])
    rule_id = str(create_rule('My rule', team_id)['id'])

    role = 'editor'
    user_id = str(create_user(role)['id'])
    create_grant(team_id, user_id, role)
    client.login(role)

    resp = client.put('/v1/teams/{}/rules/{}'.format(team_id, rule_id), data=json.dumps({'name': test_input}))
    assert resp.status_code == 400

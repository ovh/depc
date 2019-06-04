import json

from unittest.mock import PropertyMock, patch

def test_list_teams_authorization(client):
    resp = client.get('/v1/teams')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams')
    assert resp.status_code == 200


def test_list_teams(client, create_team):
    client.login('depc')
    resp = client.get('/v1/teams')
    assert len(resp.json['teams']) == 0

    create_team('My team')
    resp = client.get('/v1/teams')
    assert len(resp.json['teams']) == 1
    assert resp.json['teams'][0]['name'] == 'My team'

    for i in range(9):
        create_team('Team {}'.format(i))
    resp = client.get('/v1/teams')
    assert len(resp.json['teams']) == 10


def test_get_team_authorization(client, create_team):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}'.format(team_id))
    assert resp.status_code == 200


def test_get_team(client, create_team):
    client.login('depc')

    resp = client.get('/v1/teams/404')
    assert resp.status_code == 404

    team_id = str(create_team('My team')['id'])
    resp = client.get('/v1/teams/{}'.format(team_id))
    assert resp.status_code == 200
    assert resp.json['name'] == 'My team'


def test_get_grants_authorization(client, create_team):
    client.login('depc')
    team_id = str(create_team('My team')['id'])

    client.logout()
    resp = client.get('/v1/teams/{}/grants'.format(team_id))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/teams/{}/grants'.format(team_id))
    assert resp.status_code == 200


def test_get_grants(client, create_team, create_user, create_grant):
    client.login('depc')
    team_id = str(create_team('My team')['id'])
    resp = client.get('/v1/teams/{}/grants'.format(team_id))
    assert resp.json == []

    user_id = str(create_user('john')['id'])
    create_grant(team_id, user_id, 'member')

    resp = client.get('/v1/teams/{}/grants'.format(team_id))
    assert resp.json == [{'role': 'member', 'user': 'john'}]


def test_put_grants_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    resp = client.put(
        '/v1/teams/{}/grants'.format(team_id),
        data=json.dumps({'grants': [{'user': 'foo', 'role': 'member'}]})
    )
    assert resp.status_code == 401

    roles = {'member': 403, 'editor': 403, 'manager': 200}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.put(
            '/v1/teams/{}/grants'.format(team_id),
            data=json.dumps({'grants': [{'user': 'foo', 'role': 'member'}]})
        )
        assert resp.status_code == status


def test_put_grants_simple(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.put(
        '/v1/teams/{}/grants'.format(team_id),
        data=json.dumps({})
    )
    assert resp.raises_required_property('grants')

    resp = client.put(
        '/v1/teams/{}/grants'.format(team_id),
        data=json.dumps({'grants': []})
    )
    assert resp.status_code == 200
    assert resp.json == [
        {'role': 'manager', 'user': 'manager'}
    ]


def test_put_grants_multiple(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.put(
        '/v1/teams/{}/grants'.format(team_id),
        data=json.dumps({'grants': [
            {'role': 'editor', 'user': 'editor'}
        ]})
    )
    assert resp.status_code == 200
    assert resp.json == [
        {'role': 'manager', 'user': 'manager'}
    ]

    create_user('editor')
    resp = client.put(
        '/v1/teams/{}/grants'.format(team_id),
        data=json.dumps({'grants': [
            {'role': 'editor', 'user': 'editor'}
        ]})
    )
    assert resp.status_code == 200
    assert resp.json == [
        {'role': 'manager', 'user': 'manager'},
        {'role': 'editor', 'user': 'editor'}
    ]

    resp = client.put(
        '/v1/teams/{}/grants'.format(team_id),
        data=json.dumps({'grants': [
            {'role': 'member', 'user': 'manager'},
            {'role': 'editor', 'user': 'editor'}
        ]})
    )
    assert resp.status_code == 200
    assert resp.json == [
        {'role': 'member', 'user': 'manager'},
        {'role': 'editor', 'user': 'editor'}
    ]


def test_export_grafana_authorization(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])

    resp = client.get('/v1/teams/{}/export/grafana'.format(team_id))
    assert resp.status_code == 401

    roles = {'member': 403, 'editor': 403, 'manager': 200}
    for role, status in roles.items():
        user_id = str(create_user(role)['id'])
        create_grant(team_id, user_id, role)
        client.login(role)
        resp = client.get('/v1/teams/{}/export/grafana'.format(team_id))
        assert resp.status_code == status


def test_export_grafana_routing(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    client.login('manager')

    resp = client.get('/v1/teams/{}/export/grafana'.format(team_id))
    assert resp.json["grafana_template"]["title"] == "DepC QoS Summary"
    resp = client.get('/v1/teams/{}/export/grafana?view=summary'.format(team_id))
    assert resp.json["grafana_template"]["title"] == "DepC QoS Summary"
    resp = client.get('/v1/teams/{}/export/grafana?view=details'.format(team_id))
    assert resp.json["grafana_template"]["title"] == "DepC QoS Details"
    resp = client.get('/v1/teams/{}/export/grafana?view=foobar'.format(team_id))
    assert resp.json["grafana_template"]["title"] == "DepC QoS Summary"


def test_export_grafana_summary(client, create_team, create_user, create_grant, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')
    create_rule('MyRule', team_id)
    create_config(team_id, {'MyLabel': {'qos': 'rule.MyRule'}})

    client.login('manager')
    resp = client.get('/v1/teams/{}/export/grafana?view=summary'.format(team_id))

    # $$TEAMID$$ replacement
    assert team_id in resp.json["grafana_template"]["templating"]["list"][0]["query"]
    for panel in resp.json["grafana_template"]["panels"]:
        if "targets" in panel.keys():
            assert team_id in panel["targets"][0]["expr"]

    # $$MERMAIDDIAGRAM$$ replacement
    for panel in resp.json["grafana_template"]["panels"]:
        if panel["title"] == "Dependencies QoS":
            assert panel["content"] == "graph TB\n\ndepc.qos.label_name_MyLabel_[MyLabel]\n"
            break

    # $$BASEURL$$ and $$TEAMNAME$$ replacement
    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field
        for panel in resp.json["grafana_template"]["panels"]:
            if panel["id"] == 43:
                assert "http://127.0.0.1/#/teams/My team/dashboard/$label" in panel["content"]
                break


def test_export_grafana_details(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')

    client.login('manager')
    resp = client.get('/v1/teams/{}/export/grafana?view=details'.format(team_id))

    # $$TEAMID$$ replacement
    assert team_id in resp.json["grafana_template"]["templating"]["list"][0]["query"]
    assert team_id in resp.json["grafana_template"]["templating"]["list"][1]["query"]

    for panel in resp.json["grafana_template"]["panels"]:
        if "targets" in panel.keys():
            assert team_id in panel["targets"][0]["expr"]

    # $$BASEURL$$ and $$TEAMNAME$$ replacement
    with patch('tests.conftest.DepcResponse.KEYS_TO_REMOVE', new_callable=PropertyMock) as a:
        a.return_value = []  # We need the `id` field
        for panel in resp.json["grafana_template"]["panels"]:
            if panel["id"] == 22:
                assert "http://127.0.0.1/#/teams/My team/dashboard/$label/$node" in panel["content"]
                break


def test_export_grafrana_without_metas(client, create_team, create_user, create_grant):
    team_id = str(create_team('My team')['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')

    client.login('manager')
    resp = client.get('/v1/teams/{}/export/grafana'.format(team_id))

    assert "metas" in resp.json
    assert resp.json["metas"] == {}


def test_export_grafrana_with_metas(client, create_team, create_user, create_grant):
    payload = {"url": "foo", "token": "bar"}
    team_id = str(create_team('My team', {"grafana": payload})['id'])
    user_id = str(create_user('manager')['id'])
    create_grant(team_id, user_id, 'manager')

    client.login('manager')
    resp = client.get('/v1/teams/{}/export/grafana'.format(team_id))

    assert "metas" in resp.json
    assert resp.json["metas"] == payload

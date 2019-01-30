def test_pong(client):
    resp = client.get('/v1/ping')
    assert resp.status_code == 200
    assert resp.json == {'message': 'pong'}

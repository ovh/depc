def test_list_news_authorization(client):
    resp = client.get('/v1/news')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/news')
    assert resp.status_code == 200


def test_list_news(client, create_news):
    client.login('depc')
    resp = client.get('/v1/news')
    assert resp.json == {"news": []}

    create_news("First news", "Lorem ipsum")
    resp = client.get('/v1/news')
    assert resp.json == {
        'news': [{
            'message': 'Lorem ipsum',
            'title': 'First news'
        }]
    }


def test_list_limited_news(client, create_news):
    client.login('depc')
    resp = client.get('/v1/news')
    assert resp.json == {"news": []}

    create_news("First news", "Lorem ipsum")
    create_news("Second news", "Lorem ipsum")
    create_news("Third news", "Lorem ipsum")

    resp = client.get('/v1/news')
    assert len(resp.json["news"]) == 3

    resp = client.get('/v1/news?limit=2')
    assert len(resp.json["news"]) == 2

    resp = client.get('/v1/news?limit=foobar')
    assert len(resp.json["news"]) == 3

    resp = client.get('/v1/news?limit=1')
    assert len(resp.json["news"]) == 1
    assert resp.json["news"][0]["title"] == "Third news"


def test_list_unread_news(client, create_news):
    client.login('depc')
    first = create_news("First news", "Lorem ipsum")
    second = create_news("Second news", "Lorem ipsum")
    third = create_news("Third news", "Lorem ipsum")

    resp = client.get('/v1/news?unread=1')
    assert len(resp.json["news"]) == 3

    client.get('/v1/news/{}'.format(first["id"]))
    resp = client.get('/v1/news?unread=1')
    assert len(resp.json["news"]) == 2

    client.get('/v1/news/{}'.format(third["id"]))
    resp = client.get('/v1/news?unread=1')
    assert len(resp.json["news"]) == 1
    assert resp.json["news"][0]["title"] == second["title"]

    client.login('another.user')
    resp = client.get('/v1/news?unread=1')
    assert len(resp.json["news"]) == 3


def test_get_new_authorization(client, create_news):
    news = create_news("My news", "Lorem ipsum")
    resp = client.get('/v1/news/{}'.format(news["id"]))
    assert resp.status_code == 401

    client.login('depc')
    resp = client.get('/v1/news/{}'.format(news["id"]))
    assert resp.status_code == 200
    assert resp.json["title"] == "My news"


def test_get_new(client, create_news):
    client.login('depc')
    resp = client.get('/v1/news/notfound')
    assert resp.status_code == 404

    news = create_news("First news", "Lorem ipsum")
    resp = client.get('/v1/news/{}'.format(news["id"]))
    assert resp.status_code == 200
    assert resp.json["title"] == news["title"]


def test_clear_news_authorization(client, create_news):
    resp = client.delete('/v1/news')
    assert resp.status_code == 401

    client.login('depc')
    resp = client.delete('/v1/news')
    assert resp.status_code == 200
    assert resp.json == {}


def test_clear_news(client, create_news):
    client.login('depc')
    for i in range(10):
        create_news("News {}".format(i), "Lorem ipsum")
    resp = client.get('/v1/news?unread=1')
    assert len(resp.json["news"]) == 10

    resp = client.delete('/v1/news')
    assert resp.status_code == 200
    assert resp.json == {}

    resp = client.get('/v1/news?unread=1')
    assert len(resp.json["news"]) == 0

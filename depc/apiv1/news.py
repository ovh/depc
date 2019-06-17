from flask import jsonify, request
from flask_login import login_required

from depc.apiv1 import api, format_object
from depc.controllers.news import NewsController


VISIBLE = ["title", "message"]


def format_news(news):
    t = format_object(news, VISIBLE)
    return t


@api.route("/news")
@login_required
def list_news():
    """Return the list of news.

    .. :quickref: GET; Return the list of news.

    **Example request**:

    .. sourcecode:: http

      GET /news HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "news": [{
          "id": "28875e88-b66c-4fd3-9faa-cae8a5e408a0",
          "createdAt": "2019-06-17T16:47:05Z",
          "updatedAt": "2019-06-17T16:47:05Z",
          "title": "Hello world",
          "message": "This is a great news !"
        }]
      }

    :param unread: Returns unread news for the authenticated user
    :param limit: Limit the number of results
    :resheader Content-Type: application/json
    :status 200: list of news
    """
    limit = request.args.get("limit", None)
    unread = request.args.get("unread", False)

    news = NewsController.list(limit, unread)
    return jsonify({"news": [format_news(n) for n in news]}), 200


@api.route("/news/<news_id>")
@login_required
def get_news(news_id):
    """Return a specific news.

    .. :quickref: GET; Return a specific news.

    **Example request**:

    .. sourcecode:: http

      GET /news/28875e88-b66c-4fd3-9faa-cae8a5e408a0 HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "id": "28875e88-b66c-4fd3-9faa-cae8a5e408a0",
        "createdAt": "2019-06-17T16:47:05Z",
        "updatedAt": "2019-06-17T16:47:05Z",
        "title": "Hello world",
        "message": "This is a great news !"
      }

    :resheader Content-Type: application/json
    :status 200: the news
    """
    news = NewsController.get(filters={"News": {"id": news_id}})
    return jsonify(format_news(news)), 200


@api.route("/news", methods=["DELETE"])
@login_required
def clear_news():
    """Mark all news as read for the authenticated user.

    .. :quickref: DELETE; Mark all news as read for the authenticated user.

    **Example request**:

    .. sourcecode:: http

      DELETE /news/28875e88-b66c-4fd3-9faa-cae8a5e408a0 HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {}

    :resheader Content-Type: application/json
    :status 200: the news has been read.
    """
    return jsonify(NewsController.clear()), 200

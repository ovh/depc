from flask import abort, jsonify
from flask_login import login_required

from depc.apiv1 import api, format_object, get_payload, conf_to_kafka
from depc.controllers import NotFoundError
from depc.controllers.sources import SourceController
from depc.sources import BaseSource
from depc.users import TeamPermission

VISIBLE = ["name", "plugin", "checks"]


def format_source(source, config=False):
    visible = list(VISIBLE)
    if config:
        visible.append("configuration")
    s = format_object(source, visible)
    return s


@api.route("/sources")
@login_required
def list_available_sources():
    """Return the available sources.

    .. :quickref: GET; Return the available sources.

    **Example request**:

    .. sourcecode:: http

      GET /sources HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "sources": [{
          "name": "OpenTSDB",
          "description": "Use an OpenTSDB database to launch your queries.",
          "type": "object",
          "required": ["url", "credentials"],
          "schema": {
            "properties": {
              "credentials": {
                "description": "The credentials used authenticate the queries.",
                "title": "Credentials",
                "type": "string"
              },
              "url": {
                "description": "The url used to query the database.",
                "title": "Url",
                "type": "string"
              }
            },
          },
          "form": [{
            "key": "url",
            "placeholder": "http://127.0.0.1"
          }, {
            "key": "credentials",
            "placeholder": "foo:bar"
          }]
        }]
      }

    :resheader Content-Type: application/json
    :status 200: list of available sources
    """
    sources = BaseSource.available_sources()
    return jsonify({"sources": sources}), 200


@api.route("/sources/<source_name>")
@login_required
def get_source_info(source_name):
    """Return a specific source.

    .. :quickref: GET; Return a specific source.

    **Example request**:

    .. sourcecode:: http

      GET /sources/OpenTSDB HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "name": "OpenTSDB",
        "description": "Use an OpenTSDB database to launch your queries.",
        "type": "object",
        "required": ["url", "credentials"],
        "schema": {
          "properties": {
            "credentials": {
              "description": "The credentials used authenticate the queries.",
              "title": "Credentials",
              "type": "string"
            },
            "url": {
              "description": "The url used to query the database.",
              "title": "Url",
              "type": "string"
            }
          },
        },
        "form": [{
          "key": "url",
          "placeholder": "http://127.0.0.1"
        }, {
          "key": "credentials",
          "placeholder": "foo:bar"
        }]
      }

    :resheader Content-Type: application/json
    :status 200: the source
    """
    try:
        checks = BaseSource.source_information(source_name)
    except NotImplementedError as e:
        raise NotFoundError(str(e))

    return jsonify(checks), 200


@api.route("/sources/<source_name>/checks")
@login_required
def list_available_checks(source_name):
    """Return the checks of a source.

    .. :quickref: GET; Return the checks of a source.

    **Example request**:

    .. sourcecode:: http

      GET /sources/OpenTSDB/checks HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "checks": [{
          "name": "Threshold",
          "description": "This check executes a query on an OpenTSDB : every datapoints which is above a critical threshold lower the QOS.",
          "required": ["query", "threshold"],
          "type": "object",
          "form": [{
            "key": "query",
            "type": "codemirror"
          }, {
            "key": "threshold",
            "placeholder": "Ex: 500"
          }],
          "schema": {
            "additionalProperties": false,
              "properties": {
                "query": {
                  "description": "Query must return 1 or more timeserie(s).",
                  "title": "OpenTSDB query",
                  "type": "string"
                },
                "threshold": {
                  "description": "The QOS will be lowered for every values strictly superior to this threshold.",
                  "title": "Threshold",
                  "type": "string"
                }
              }
            }
          }
        ]
      }

    :resheader Content-Type: application/json
    :status 200: the checks of the source
    """
    checks = BaseSource.available_checks(source_name)
    return jsonify({"checks": checks}), 200


@api.route("/sources/<source_name>/checks/<check_name>")
@login_required
def check_info(source_name, check_name):
    """Return a check from a source.

    .. :quickref: GET; Return a check from a source.

    **Example request**:

    .. sourcecode:: http

      GET /sources/OpenTSDB/checks/Threshold HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "name": "Threshold",
        "description": "This check executes a query on an OpenTSDB : every datapoints which is above a critical threshold lower the QOS.",
        "required": ["query", "threshold"],
        "type": "object",
        "form": [{
          "key": "query",
          "type": "codemirror"
        }, {
          "key": "threshold",
          "placeholder": "Ex: 500"
        }],
        "schema": {
          "additionalProperties": false,
          "properties": {
            "query": {
              "description": "Query must return 1 or more timeserie(s).",
              "title": "OpenTSDB query",
              "type": "string"
            },
            "threshold": {
              "description": "The QOS will be lowered for every values strictly superior to this threshold.",
              "title": "Threshold",
              "type": "string"
            }
          }
        }
      }

    :resheader Content-Type: application/json
    :status 200: the check
    """
    try:
        checks = BaseSource.check_information(source_name, check_name)
    except NotImplementedError as e:
        raise NotFoundError(str(e))

    return jsonify(checks), 200


@api.route("/teams/<team_id>/sources")
@login_required
def list_sources(team_id):
    """List the sources of a team.

    .. :quickref: GET; List the sources of a team.

    **Example request**:

    .. sourcecode:: http

      GET /teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "sources": [
           {
             "checks": [{
               "created_at": "2018-05-17T11:52:25Z",
               "id": "86ee5bdb-7088-400c-8654-a162f18b0710",
               "name": "Server Ping",
               "parameters": {
                 "metric": "depc.tutorial.ping",
                 "threshold": 20
               },
               "source_id": "672d82d7-1970-48cd-a690-20f5daf303cf",
               "type": "Threshold",
               "updated_at": "2018-11-12T17:41:11Z"
             }],
             "configuration": {},
             "createdAt": "2018-05-16T11:38:46Z",
             "id": "672d82d7-1970-48cd-a690-20f5daf303cf",
             "name": "My source",
             "plugin": "Fake",
             "updatedAt": "2019-01-15T13:33:22Z"
          }
        ]
      }

    :resheader Content-Type: application/json
    :status 200: the list of sources
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    sources = SourceController.list(filters={"Source": {"team_id": team_id}})

    return (
        jsonify(
            {
                "sources": [
                    format_source(s, config=TeamPermission.is_manager(team_id))
                    for s in sources
                ]
            }
        ),
        200,
    )


@api.route("/teams/<team_id>/sources/<source_id>")
@login_required
def get_source(team_id, source_id):
    """Get a source from a team.

    .. :quickref: GET; Get a source from a team.

    **Example request**:

    .. sourcecode:: http

      GET /teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources/672d82d7-1970-48cd-a690-20f5daf303cf HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
         "checks": [{
           "created_at": "2018-05-17T11:52:25Z",
           "id": "86ee5bdb-7088-400c-8654-a162f18b0710",
           "name": "Server Ping",
           "parameters": {
             "metric": "depc.tutorial.ping",
             "threshold": 20
           },
           "source_id": "672d82d7-1970-48cd-a690-20f5daf303cf",
           "type": "Threshold",
           "updated_at": "2018-11-12T17:41:11Z"
         }],
         "configuration": {},
         "createdAt": "2018-05-16T11:38:46Z",
         "id": "672d82d7-1970-48cd-a690-20f5daf303cf",
         "name": "My source",
         "plugin": "Fake",
         "updatedAt": "2019-01-15T13:33:22Z"
      }

    :resheader Content-Type: application/json
    :status 200: the list of sources
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    source = SourceController.get(
        filters={"Source": {"id": source_id, "team_id": team_id}}
    )

    return (
        jsonify(format_source(source, config=TeamPermission.is_manager(team_id))),
        200,
    )


@api.route(
    "/teams/<team_id>/sources",
    methods=["POST"],
    request_schema=("v1_source", "source_input"),
)
@login_required
@conf_to_kafka
def post_source(team_id):
    """Add a new source.

    .. :quickref: POST; Add a new source.

    **Example request**:

    .. sourcecode:: http

      POST /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "name": "My source",
        "plugin": "Fake",
        "configuration": {}
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 201 CREATED

      {
        "checks": [],
        "configuration": {},
        "createdAt": "2019-01-21T14:08:22Z",
        "id": "e2c1c635-2d7c-4881-83d1-e4e7027ac7a2",
        "name": "My source",
        "plugin": "Fake",
        "updatedAt": "2019-01-21T14:08:22Z"
      }

    :resheader Content-Type: application/json
    :status 201: the created source
    """
    if not TeamPermission.is_manager(team_id):
        abort(403)

    payload = get_payload()
    payload["team_id"] = team_id
    source = SourceController.create(payload)
    return jsonify(format_source(source, True)), 201


@api.route(
    "/teams/<team_id>/sources/<source_id>",
    methods=["PUT"],
    request_schema=("v1_source", "source_update"),
)
@login_required
@conf_to_kafka
def put_source(team_id, source_id):
    """Edit an existing source.

    .. :quickref: PUT; Edit an existing source.

    **Example request**:

    .. sourcecode:: http

      PUT /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources/e2c1c635-2d7c-4881-83d1-e4e7027ac7a2 HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "name": "My edited source"
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "checks": [],
        "configuration": {},
        "createdAt": "2019-01-21T14:08:22Z",
        "id": "e2c1c635-2d7c-4881-83d1-e4e7027ac7a2",
        "name": "My edited source",
        "plugin": "Fake",
        "updatedAt": "2019-01-21T14:21:24Z"
      }

    :resheader Content-Type: application/json
    :status 200: the edited source
    """
    if not TeamPermission.is_manager(team_id):
        abort(403)

    payload = get_payload()
    source = SourceController.update(
        payload, {"Source": {"id": source_id, "team_id": team_id}}
    )
    return jsonify(format_source(source, True)), 200


@api.route("/teams/<team_id>/sources/<source_id>", methods=["DELETE"])
@login_required
@conf_to_kafka
def delete_source(team_id, source_id):
    """Delete a source.

    .. :quickref: DELETE; Delete a source.

    **Example request**:

    .. sourcecode:: http

      DELETE /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources/e2c1c635-2d7c-4881-83d1-e4e7027ac7a2 HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {}

    :resheader Content-Type: application/json
    :status 200: the source has been deleted
    """
    if not TeamPermission.is_manager(team_id):
        abort(403)

    SourceController.delete(filters={"Source": {"id": source_id, "team_id": team_id}})
    return jsonify({}), 200

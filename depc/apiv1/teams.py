from flask import abort, jsonify, request
from flask_login import login_required

from depc.apiv1 import api, format_object, get_payload
from depc.controllers.teams import TeamController
from depc.users import TeamPermission

VISIBLE = ["name", "rules", "managers", "editors", "members"]


def format_team(team):
    t = format_object(team, VISIBLE)
    return t


@api.route("/teams")
@login_required
def list_teams():
    """Return the list of teams.

    .. :quickref: GET; Return the list of teams.

    **Example request**:

    .. sourcecode:: http

      GET /teams HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        'teams': [{
          'createdAt': '2019-01-15T10:24:35Z',
          'id': '5b513051-74b4-4eea-9739-5c5053c3d37c',
          'name': 'My team',
          'updatedAt': '2019-01-15T10:24:35Z'
        }]
      }

    :resheader Content-Type: application/json
    :status 200: list of teams
    """
    name = request.args.get("name", None)

    # Search team by name
    if name:
        team = TeamController.get(filters={"Team": {"name": name}})
        return jsonify(format_team(team)), 200

    # Otherwise list of the teams
    teams = TeamController.list()
    return jsonify({"teams": [format_team(s) for s in teams]}), 200


@api.route("/teams/<team_id>")
@login_required
def get_team(team_id):
    """Return a specific team.

    .. :quickref: GET; Return a specific team.

    **Example request**:

    .. sourcecode:: http

      GET /teams/76b96ead-a7ed-447b-8fa6-26b57bc571e5 HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        'createdAt': '2019-01-15T11:44:23Z',
        'id': '76b96ead-a7ed-447b-8fa6-26b57bc571e5',
        'name': 'My team',
        'updatedAt': '2019-01-15T11:44:23Z'
      }

    :resheader Content-Type: application/json
    :status 200: the team
    """
    team = TeamController.get(filters={"Team": {"id": team_id}})
    return jsonify(format_team(team)), 200


@api.route("/teams/<team_id>/grants")
@login_required
def get_grants(team_id):
    """Return the grants of a team.

    .. :quickref: GET; Return the grants of a team.

    **Example request**:

    .. sourcecode:: http

      GET /teams/76b96ead-a7ed-447b-8fa6-26b57bc571e5/grants HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      [
        {
          'role': 'member',
          'user': 'john'
        }
      ]

    :resheader Content-Type: application/json
    :status 200: the grants
    """
    grants = TeamController.get_grants(team_id=team_id)
    return jsonify(grants), 200


@api.route(
    "/teams/<team_id>/grants",
    methods=["PUT"],
    request_schema=("v1_team", "grants_input"),
)
@login_required
def put_grants(team_id):
    """Change the grants of a team.

    .. :quickref: PUT; Change the grants of a team.

    **Example request**:

    .. sourcecode:: http

      PUT /teams/76b96ead-a7ed-447b-8fa6-26b57bc571e5/grants HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        'grants': [{
          'user': 'foo',
          'role': 'member'
        }]
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      [
        {
          'role': 'member',
          'user': 'john'
        }
      ]

    :resheader Content-Type: application/json
    :status 200: the grants
    """
    if not TeamPermission.is_manager(team_id):
        abort(403)

    payload = get_payload()
    grants = TeamController.put_grants(team_id=team_id, grants=payload["grants"])
    return jsonify(grants)


@api.route("/teams/<team_id>/export/grafana")
@login_required
def team_export_grafana(team_id):
    """Export the QoS into Grafana.

    .. :quickref: GET; Export the QoS into Grafana.

    **Example request**:

    .. sourcecode:: http

      GET /teams/76b96ead-a7ed-447b-8fa6-26b57bc571e5/export/grafana HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "metas": {
          "url": "https://warp-endpoint.local",
          "token": "foobar"
        },
        "grafana_template": {
          // Grafana JSON format
          // See: https://grafana.com/docs/reference/export_import/
        }
      }

    :resheader Content-Type: application/json
    :status 200: the JSON to import in Grafana
    """
    if not TeamPermission.is_manager(team_id):
        abort(403)

    view = request.args.get("view", "summary")
    if view not in ["summary", "details"]:
        view = "summary"

    return jsonify(TeamController.export_grafana(team_id, view))

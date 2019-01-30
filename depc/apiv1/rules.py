from flask import abort, jsonify
from flask_login import login_required

from depc.apiv1 import api, format_object, get_payload
from depc.controllers.rules import RuleController
from depc.users import TeamPermission

VISIBLE = ["name", "description", "checks"]


def format_rule(rule):
    s = format_object(rule, VISIBLE)
    return s


@api.route("/teams/<team_id>/rules")
@login_required
def list_rules(team_id):
    """List the rules of a team.

    .. :quickref: GET; List the rules of a team.

    **Example request**:

    .. sourcecode:: http

      GET /teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/rules HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "rules": [{
          "checks": [],
          "createdAt": "2018-05-17T12:01:09Z",
          "description": "Compute the QOS of our servers",
          "id": "ff130e9b-d226-4465-9612-a93e12799091",
          "name": "Servers",
          "updatedAt": "2018-11-09T15:33:06Z"
        }]
      }

    :resheader Content-Type: application/json
    :status 200: the list of rules
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    rules = RuleController.list(filters={"Rule": {"team_id": team_id}})
    return jsonify({"rules": [format_rule(r) for r in rules]}), 200


@api.route("/teams/<team_id>/rules/<rule_id>")
@login_required
def get_rule(team_id, rule_id):
    """Return a specific rule.

    .. :quickref: GET; Return a specific rule.

    **Example request**:

    .. sourcecode:: http

      GET /teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/rules/ff130e9b-d226-4465-9612-a93e12799091 HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "checks": [],
        "createdAt": "2018-05-17T12:01:09Z",
        "description": "Compute the QOS of our servers",
        "id": "ff130e9b-d226-4465-9612-a93e12799091",
        "name": "Servers",
        "updatedAt": "2018-11-09T15:33:06Z"
      }

    :resheader Content-Type: application/json
    :status 200: the rule
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    rule = RuleController.get(filters={"Rule": {"id": rule_id, "team_id": team_id}})
    return jsonify(format_rule(rule)), 200


@api.route(
    "/teams/<team_id>/rules", methods=["POST"], request_schema=("v1_rule", "rule_input")
)
@login_required
def post_rule(team_id):
    """Add a new rule.

    .. :quickref: POST; Add a new rule.

    **Example request**:

    .. sourcecode:: http

      POST /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/rules HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "name": "Servers",
        "description": "Compute the QOS of our servers"
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 201 CREATED

      {
        "checks": [],
        "createdAt": "2018-05-17T12:01:09Z",
        "description": "Compute the QOS of our servers",
        "id": "ff130e9b-d226-4465-9612-a93e12799091",
        "name": "Servers",
        "updatedAt": "2018-11-09T15:33:06Z"
      }

    :resheader Content-Type: application/json
    :status 201: the created rule
    """
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    payload["team_id"] = team_id
    rule = RuleController.create(payload)
    return jsonify(format_rule(rule)), 201


@api.route(
    "/teams/<team_id>/rules/<rule_id>",
    methods=["PUT"],
    request_schema=("v1_rule", "rule_update"),
)
@login_required
def put_rule(team_id, rule_id):
    """Edit an existing rule.

    .. :quickref: PUT; Edit an existing rule.

    **Example request**:

    .. sourcecode:: http

      PUT /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/rules/ff130e9b-d226-4465-9612-a93e12799091 HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "name": "My edited rule"
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "checks": [],
        "createdAt": "2018-05-17T12:01:09Z",
        "description": "Compute the QOS of our servers",
        "id": "ff130e9b-d226-4465-9612-a93e12799091",
        "name": "My edited rule",
        "updatedAt": "2018-11-09T15:33:06Z"
      }

    :resheader Content-Type: application/json
    :status 200: the edited rule
    """
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    rule = RuleController.update(payload, {"Rule": {"id": rule_id, "team_id": team_id}})
    return jsonify(format_rule(rule)), 200


@api.route("/teams/<team_id>/rules/<rule_id>", methods=["DELETE"])
@login_required
def delete_rule(team_id, rule_id):
    """Delete a rule.

    .. :quickref: DELETE; Delete a rule.

    **Example request**:

    .. sourcecode:: http

      DELETE /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/rules/ff130e9b-d226-4465-9612-a93e12799091 HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {}

    :resheader Content-Type: application/json
    :status 200: the rule has been deleted
    """
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    RuleController.delete(filters={"Rule": {"id": rule_id, "team_id": team_id}})
    return jsonify({}), 200


@api.route(
    "/teams/<team_id>/rules/<rule_id>/execute",
    methods=["POST"],
    request_schema=("v1_rule", "rule_execute"),
)
@login_required
def execute_rule(team_id, rule_id):
    """

    .. :quickref: POST; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    payload = get_payload()

    # Does the team owns the rule
    RuleController.get({"Rule": {"id": rule_id, "team_id": team_id}})

    result = RuleController.execute(rule_id, **payload)
    return jsonify({"result": result}), 200

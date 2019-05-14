from flask import abort, jsonify
from flask_login import login_required

from depc.apiv1 import api, format_object, get_payload, conf_to_kafka
from depc.controllers.checks import CheckController
from depc.controllers.rules import RuleController
from depc.controllers.sources import SourceController
from depc.users import TeamPermission

VISIBLE = ["name", "type", "parameters"]


def format_check(check):
    s = format_object(check, VISIBLE)
    return s


@api.route("/teams/<team_id>/sources/<source_id>/checks")
@login_required
def list_source_checks(team_id, source_id):
    """List the checks of a source.

    .. :quickref: GET; List the checks of a source.

    **Example request**:

    .. sourcecode:: http

      GET /teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources/e2c1c635-2d7c-4881-83d1-e4e7027ac7a2/checks HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

        {
          'checks': [{
            'name': 'My check',
            'parameters': {'metric': 'foo', 'threshold': 100},
            'type': 'Threshold'
          }]
        }

    :resheader Content-Type: application/json
    :status 200: the list of checks
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    team = SourceController.get(
        filters={"Source": {"id": source_id, "team_id": team_id}}
    )
    return jsonify({"checks": [format_check(c) for c in team["checks"]]}), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/checks",
    methods=["POST"],
    request_schema=("v1_check", "check_input"),
)
@login_required
@conf_to_kafka
def post_source_check(team_id, source_id):
    """Add a new check.

    .. :quickref: POST; Add a new check.

    **Example request**:

    .. sourcecode:: http

      POST /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/sources/e2c1c635-2d7c-4881-83d1-e4e7027ac7a2/checks HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "name": "My check",
        "type": "Threshold",
        "parameters": {
          "metric": "foo",
          "threshold": 100
        }
      }

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 201 CREATED

      {
        'name': 'My check',
        'parameters': {
          'metric': 'foo',
          'threshold': 100
        },
        'type': 'Threshold'
      }

    :resheader Content-Type: application/json
    :status 201: the created check
    """
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    payload["source_id"] = source_id

    source = CheckController.create(payload)
    return jsonify(format_check(source)), 201


@api.route(
    "/teams/<team_id>/sources/<source_id>/checks/<check_id>",
    methods=["PUT"],
    request_schema=("v1_check", "check_update"),
)
@login_required
@conf_to_kafka
def put_source_check(team_id, source_id, check_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    check = CheckController.update(
        payload, {"Check": {"id": check_id, "source_id": source_id}}
    )
    return jsonify(format_check(check)), 200


@api.route("/teams/<team_id>/sources/<source_id>/checks/<check_id>", methods=["DELETE"])
@login_required
def delete_source_check(team_id, source_id, check_id):
    """

    .. :quickref: DELETE; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    check = CheckController.delete(
        filters={"Check": {"id": check_id, "source_id": source_id}}
    )
    return jsonify(format_check(check)), 200


@api.route("/teams/<team_id>/rules/<rule_id>/checks")
@login_required
def list_rule_checks(team_id, rule_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    rule = RuleController.get(filters={"Rule": {"id": rule_id, "team_id": team_id}})
    return jsonify({"checks": [format_check(r) for r in rule["checks"]]}), 200


@api.route(
    "/teams/<team_id>/rules/<rule_id>/checks",
    methods=["PUT"],
    request_schema=("v1_rule", "rule_change_checks"),
)
@login_required
@conf_to_kafka
def put_rule_checks(team_id, rule_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    rule = RuleController.update_checks(rule_id=rule_id, checks_id=payload["checks"])
    return jsonify({"checks": [format_check(r) for r in rule["checks"]]}), 200

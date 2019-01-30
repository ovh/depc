from flask import abort, jsonify
from flask_login import login_required

from depc.apiv1 import api, format_object, get_payload
from depc.controllers.variables import VariableController
from depc.users import TeamPermission

VISIBLE = ["name", "value", "type", "expression"]


def format_variable(source):
    visible = list(VISIBLE)
    s = format_object(source, visible)
    return s


@api.route("/teams/<team_id>/variables")
@login_required
def list_team_variables(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variables = VariableController.list(
        filters={
            "Variable": {
                "team_id": team_id,
                "rule_id": None,
                "source_id": None,
                "check_id": None,
            }
        }
    )

    return jsonify([format_variable(v) for v in variables]), 200


@api.route("/teams/<team_id>/rules/<rule_id>/variables")
@login_required
def list_rule_variables(team_id, rule_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variables = VariableController.list(
        filters={
            "Variable": {
                "team_id": team_id,
                "rule_id": rule_id,
                "source_id": None,
                "check_id": None,
            }
        }
    )

    return jsonify([format_variable(v) for v in variables]), 200


@api.route("/teams/<team_id>/sources/<source_id>/variables")
@login_required
def list_source_variables(team_id, source_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variables = VariableController.list(
        filters={
            "Variable": {
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": None,
            }
        }
    )

    return jsonify([format_variable(v) for v in variables]), 200


@api.route("/teams/<team_id>/sources/<source_id>/checks/<check_id>/variables")
@login_required
def list_check_variables(team_id, source_id, check_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variables = VariableController.list(
        filters={
            "Variable": {
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": check_id,
            }
        }
    )

    return jsonify([format_variable(v) for v in variables]), 200


@api.route("/teams/<team_id>/variables/<variable_id>")
@login_required
def get_team_variable(team_id, variable_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variable = VariableController.get(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": None,
                "check_id": None,
            }
        }
    )

    return jsonify(format_variable(variable)), 200


@api.route("/teams/<team_id>/rules/<rule_id>/variables/<variable_id>")
@login_required
def get_rule_variable(team_id, rule_id, variable_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variable = VariableController.get(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": rule_id,
                "source_id": None,
                "check_id": None,
            }
        }
    )

    return jsonify(format_variable(variable)), 200


@api.route("/teams/<team_id>/sources/<source_id>/variables/<variable_id>")
@login_required
def get_source_variable(team_id, source_id, variable_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variable = VariableController.get(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": None,
            }
        }
    )

    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/checks/<check_id>/variables/<variable_id>"
)
@login_required
def get_check_variable(team_id, source_id, check_id, variable_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    variable = VariableController.get(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": check_id,
            }
        }
    )

    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/variables",
    methods=["POST"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def post_team_variable(team_id):
    """

    .. :quickref: POST; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    payload.update({"team_id": team_id})
    variable = VariableController.create(payload)
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/rules/<rule_id>/variables",
    methods=["POST"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def post_rule_variable(team_id, rule_id):
    """

    .. :quickref: POST; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    payload.update({"team_id": team_id, "rule_id": rule_id})
    variable = VariableController.create(payload)
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/variables",
    methods=["POST"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def post_source_variable(team_id, source_id):
    """

    .. :quickref: POST; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    payload.update({"team_id": team_id, "source_id": source_id})
    variable = VariableController.create(payload)
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/checks/<check_id>/variables",
    methods=["POST"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def post_check_variable(team_id, source_id, check_id):
    """

    .. :quickref: POST; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    payload.update({"team_id": team_id, "source_id": source_id, "check_id": check_id})
    variable = VariableController.create(payload)
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/variables/<variable_id>",
    methods=["PUT"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def put_team_variable(team_id, variable_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    variable = VariableController.update(
        payload,
        {
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": None,
                "check_id": None,
            }
        },
    )
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/rules/<rule_id>/variables/<variable_id>",
    methods=["PUT"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def put_rule_variable(team_id, rule_id, variable_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    variable = VariableController.update(
        payload,
        {
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": rule_id,
                "source_id": None,
                "check_id": None,
            }
        },
    )
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/variables/<variable_id>",
    methods=["PUT"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def put_source_variable(team_id, source_id, variable_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    variable = VariableController.update(
        payload,
        {
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": None,
            }
        },
    )
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/checks/<check_id>/variables/<variable_id>",
    methods=["PUT"],
    request_schema=("v1_variable", "variable_input"),
)
@login_required
def put_check_variable(team_id, source_id, check_id, variable_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    payload = get_payload()
    variable = VariableController.update(
        payload,
        {
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": check_id,
            }
        },
    )
    return jsonify(format_variable(variable)), 200


@api.route("/teams/<team_id>/variables/<variable_id>", methods=["DELETE"])
@login_required
def delete_team_variable(team_id, variable_id):
    """

    .. :quickref: DELETE; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    variable = VariableController.delete(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": None,
                "check_id": None,
            }
        }
    )
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/rules/<rule_id>/variables/<variable_id>", methods=["DELETE"]
)
@login_required
def delete_rule_variable(team_id, rule_id, variable_id):
    """

    .. :quickref: DELETE; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    variable = VariableController.delete(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": rule_id,
                "source_id": None,
                "check_id": None,
            }
        }
    )
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/variables/<variable_id>", methods=["DELETE"]
)
@login_required
def delete_source_variable(team_id, source_id, variable_id):
    """

    .. :quickref: DELETE; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    variable = VariableController.delete(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": None,
            }
        }
    )
    return jsonify(format_variable(variable)), 200


@api.route(
    "/teams/<team_id>/sources/<source_id>/checks/<check_id>/variables/<variable_id>",
    methods=["DELETE"],
)
@login_required
def delete_check_variable(team_id, source_id, check_id, variable_id):
    """

    .. :quickref: DELETE; Lorem ipsum."""
    if not TeamPermission.is_manager_or_editor(team_id):
        abort(403)

    variable = VariableController.delete(
        filters={
            "Variable": {
                "id": variable_id,
                "team_id": team_id,
                "rule_id": None,
                "source_id": source_id,
                "check_id": check_id,
            }
        }
    )
    return jsonify(format_variable(variable)), 200

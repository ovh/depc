from flask import jsonify, request
from flask_login import login_required
from werkzeug.exceptions import abort

from depc.apiv1 import api
from depc.controllers.configs import ConfigController
from depc.users import TeamPermission


@api.route("/teams/<team_id>/configs/current")
@login_required
def get_current_config(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    config = ConfigController.get_current_config(team_id=team_id)
    return jsonify(config), 200


@api.route(
    "/teams/<team_id>/configs",
    methods=["POST"],
    request_schema=("v1_config", "config_input"),
)
@login_required
def put_config(team_id):
    """

    .. :quickref: POST; Lorem ipsum."""
    if not TeamPermission.is_manager(team_id):
        abort(403)

    payload = request.get_json(force=True)
    current_conf = ConfigController.create({"team_id": team_id, "data": payload})
    return jsonify(current_conf), 200


@api.route("/teams/<team_id>/configs")
@login_required
def list_configs(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    configs = ConfigController.list(
        filters={"Config": {"team_id": team_id}}, order_by="updated_at", reverse=True
    )
    return jsonify(configs), 200


@api.route("/teams/<team_id>/configs/<config_id>")
@login_required
def get_config(team_id, config_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    config = ConfigController.get(
        filters={"Config": {"team_id": team_id, "id": config_id}}
    )
    if not config:
        abort(404)

    return jsonify(config), 200


@api.route("/teams/<team_id>/configs/<config_id>/apply", methods=["PUT"])
@login_required
def revert_config(team_id, config_id):
    """

    .. :quickref: PUT; Lorem ipsum."""
    if not TeamPermission.is_manager(team_id):
        abort(403)

    config = ConfigController.revert_config(team_id=team_id, config_id=config_id)
    if not config:
        abort(404)
    return jsonify(config), 200

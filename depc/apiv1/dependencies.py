import arrow
from flask import abort, jsonify, request

from depc.apiv1 import api
from depc.controllers.dependencies import DependenciesController
from depc.users import TeamPermission


@api.route("/teams/<team_id>/labels")
def get_labels(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(DependenciesController.get_labels(team_id))


@api.route("/teams/<team_id>/labels/<label>/nodes")
def get_label_nodes(team_id, label):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(
        DependenciesController.get_label_nodes(
            team_id,
            label,
            request.args.get("name", None),
            request.args.get("limit", None),
            request.args.get("random", False),
        )
    )


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>/count")
def count_node_dependencies(team_id, label, node):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(DependenciesController.count_node_dependencies(team_id, label, node))


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>")
def get_node_dependencies(team_id, label, node):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(
        DependenciesController.get_node_dependencies(
            team_id=team_id,
            label=label,
            node=node,
            day=request.args.get("day", arrow.utcnow().format("YYYY-MM-DD")),
            filter_on_config=request.args.get("with_config", False),
            include_old_nodes=request.args.get("with_olds", False),
        )
    )


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>", methods=["DELETE"])
def delete_node(team_id, label, node):
    """

    .. :quickref: DELETE; Lorem ipsum."""
    if not TeamPermission.is_manager(team_id):
        abort(403)

    return jsonify(
        DependenciesController.delete_node(
            team_id=team_id,
            label=label,
            node=node,
            detach=request.args.get("detach", False),
        )
    )

from flask import abort, jsonify, request
from flask_login import login_required

from depc.apiv1 import api
from depc.controllers.statistics import StatisticsController
from depc.users import TeamPermission


@api.route("/teams/<team_id>/statistics")
@login_required
def get_team_statistics(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    return (
        jsonify(
            StatisticsController.get_team_statistics(
                team_id=team_id,
                start=request.args.get("start", None),
                end=request.args.get("end", None),
                label=request.args.get("label", None),
                type=request.args.get("type", None),
                sort=request.args.get("sort", "label"),
            )
        ),
        200,
    )

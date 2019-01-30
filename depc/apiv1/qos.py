import arrow
from flask import abort, jsonify, request
from flask_login import login_required

from depc.apiv1 import api
from depc.controllers.qos import QosController
from depc.controllers.worst import WorstController
from depc.users import TeamPermission


@api.route("/teams/<team_id>/qos")
@login_required
def get_team_qos(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    label = request.args.get("label", None)
    name = request.args.get("name", None)
    start = request.args.get("start", None)
    end = request.args.get("end", None)

    if name:
        data = QosController.get_team_item_qos(team_id, label, name, start, end)
    else:
        data = QosController.get_team_qos(team_id, label, start, end)

    return jsonify(data)


@api.route("/teams/<team_id>/qos/worst")
@login_required
def get_team_worst_qos(team_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    if not TeamPermission.is_user(team_id):
        abort(403)

    label = request.args.get("label", None)
    date = request.args.get("date", arrow.now().shift(days=-1).format("YYYY-MM-DD"))

    return jsonify(WorstController.get_daily_worst_items(team_id, label, date))

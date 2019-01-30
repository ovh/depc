from flask import json, jsonify, request
from flask_login import login_required

from depc.apiv1 import api
from depc.controllers.logs import LogController
from depc.extensions import redis


def format_log(log):
    log["_id"] = log["id"]
    return {"message": log}


@api.route("/results/<result_id>", methods=["GET"])
@login_required
def get_result(result_id):
    """

    .. :quickref: GET; Lorem ipsum."""
    sort = request.args.get("sort", "asc")
    limit = request.args.get("limit", 1000)

    result = redis.get(result_id)

    # Logs response
    logs = LogController.list(
        filters={"Log": {"key": result_id}},
        order_by="created_at",
        limit=limit,
        reverse=False if sort == "asc" else True,
    )

    data = {"logs": [format_log(l) for l in logs]}
    if result:
        data["qos"] = json.loads(result)

    return jsonify(data), 200

from flask import jsonify
from flask_login import login_required

from depc.apiv1 import api, format_object
from depc.controllers.users import UserController

VISIBLE = ["name", "grants"]


def format_user(user):
    s = format_object(user, VISIBLE)
    return s


@api.route("/users")
@login_required
def list_users():
    """

    .. :quickref: GET; Lorem ipsum."""
    users = UserController.list()
    return jsonify({"users": [format_user(u) for u in users]}), 200


@api.route("/users/me")
@login_required
def me():
    """

    .. :quickref: GET; Lorem ipsum."""
    user = UserController.get_current_user()
    return jsonify(format_user(user)), 200

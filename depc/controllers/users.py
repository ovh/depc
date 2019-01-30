import werkzeug.security
from flask_login import current_user

from depc.controllers import Controller, AlreadyExistError
from depc.extensions import db
from depc.models.users import User


class UserController(Controller):

    model_cls = User

    @classmethod
    def get_current_user(cls):
        user = current_user.to_dict()
        user["grants"] = {}

        for grant in current_user.grants:
            user["grants"][grant.team.name] = grant.role.name

        return user

    @classmethod
    def before_data_load(cls, data):
        if "password" in data:
            data["password"] = werkzeug.security.generate_password_hash(
                data["password"]
            )

    @classmethod
    def handle_integrity_error(cls, obj, error):
        db.session.rollback()
        if User.query.filter_by(username=obj.username).all():
            raise AlreadyExistError(
                "The user {username} already exists.", {"username": obj.username}
            )

from depc.controllers import Controller
from depc.controllers import NotFoundError
from depc.controllers.grants import GrantController
from depc.controllers.users import UserController
from depc.extensions import db
from depc.models.teams import Team
from depc.models.users import Grant


class TeamController(Controller):

    model_cls = Team

    @classmethod
    def get_grants(cls, team_id):
        team = cls._get(filters={"Team": {"id": team_id}})

        return [GrantController.resource_to_dict(g) for g in team.grants]

    @classmethod
    def put_grants(cls, team_id, grants):
        team = cls._get(filters={"Team": {"id": team_id}})

        for grant in grants:
            try:
                user_to_grant = UserController._get(
                    filters={"User": {"name": grant["user"]}}
                )
            except NotFoundError:
                # Skip the unknown users and roles
                continue

            # Search a grant with this user and this team
            exist_grant = Grant.query.filter_by(team=team, user=user_to_grant).first()

            if not exist_grant:
                exist_grant = Grant(team=team, user=user_to_grant)
                db.session.add(exist_grant)

            # Change its role
            exist_grant.role = grant["role"]
            db.session.commit()

        return [GrantController.resource_to_dict(g) for g in team.grants]

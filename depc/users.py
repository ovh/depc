from flask_login import current_user

from depc.controllers.teams import TeamController


class TeamPermission:
    @classmethod
    def _get_team(cls, team_id):
        obj = TeamController._get(filters={"Team": {"id": team_id}})

        # Add the members of the team
        team = TeamController.resource_to_dict(obj)
        team.update(
            {
                "members": [m.name for m in obj.members],
                "editors": [m.name for m in obj.editors],
                "managers": [m.name for m in obj.managers],
            }
        )
        return team

    @classmethod
    def is_user(cls, team_id):
        team = cls._get_team(team_id)
        team_users = team["members"] + team["editors"] + team["managers"]
        return current_user.name in team_users

    @classmethod
    def is_manager_or_editor(cls, team_id):
        team = cls._get_team(team_id)
        team_users = team["editors"] + team["managers"]
        return current_user.name in team_users

    @classmethod
    def is_manager(cls, team_id):
        return current_user.name in cls._get_team(team_id)["managers"]

    @classmethod
    def is_editor(cls, team_id):
        return current_user.name in cls._get_team(team_id)["editors"]

    @classmethod
    def is_member(cls, team_id):
        return current_user.name in cls._get_team(team_id)["members"]

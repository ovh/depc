import json
import re

from flask import current_app as app

from depc.controllers import Controller
from depc.controllers import NotFoundError
from depc.controllers.configs import ConfigController
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

    @classmethod
    def export_grafana(cls, team_id, view="summary"):
        team = cls._get(filters={"Team": {"id": team_id}})

        metas = team.metas if team.metas else {}
        data = {"metas": metas.get("grafana", {})}

        if view == "summary":
            data["grafana_template"] = cls.export_summary_grafana(team)
        else:
            data["grafana_template"] = cls.export_details_grafana(team)

        return data

    @classmethod
    def _generate_grafana_template(cls, team, name):
        with open("{}/{}.json".format(app.config["STATIC_DIR"], name)) as f:
            data = f.read()

            data = data.replace("$$BASEURL$$", app.config["BASE_UI_URL"])
            data = data.replace("$$TEAMID$$", str(team.id))
            data = data.replace("$$TEAMNAME$$", team.name)

        return data

    @classmethod
    def _generate_marmaid_diagram(cls, configs):
        mermaid = "graph TB\\n\\n"

        for label, config in configs.items():
            qos = config["qos"]

            # Qos by rule
            if qos.startswith("rule"):
                mermaid += "depc.qos.label_name_{label}_[{label}]\\n".format(
                    label=label
                )

            # Qos by operation or aggregation
            else:
                regex = r".*\[(.*)\]"
                match = re.search(regex, qos)
                deps = match.group(1).split(", ")

                for dep in deps:
                    mermaid += "depc.qos.label_name_{label}_[{label}] --> depc.qos.label_name_{dep}_[{dep}]\\n".format(
                        label=label, dep=dep
                    )
        return mermaid

    @classmethod
    def export_summary_grafana(cls, team):
        data = cls._generate_grafana_template(team, "grafana_summary_dashboard")

        try:
            configs = ConfigController.get_current_config(team.id)["data"]
            data = data.replace(
                "$$MERMAIDDIAGRAM$$", cls._generate_marmaid_diagram(configs)
            )
        except NotFoundError:
            data = data.replace("$$MERMAIDDIAGRAM$$", "")

        return json.loads(data)

    @classmethod
    def export_details_grafana(cls, team):
        data = cls._generate_grafana_template(team, "grafana_details_dashboard")
        return json.loads(data)

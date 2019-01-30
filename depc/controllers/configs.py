import re

from depc.controllers import Controller, NotFoundError
from depc.controllers.rules import RuleController
from depc.extensions import db
from depc.models.configs import Config


class ConfigController(Controller):
    model_cls = Config

    @classmethod
    def _join_to(cls, query, object_class):
        pass

    @classmethod
    def get_current_config(cls, team_id):
        configs = ConfigController.list(
            filters={"Config": {"team_id": team_id}},
            order_by="updated_at",
            reverse=True,
            limit=1,
        )
        config = next(iter(configs), None)

        if not config:
            raise NotFoundError("No config found.")

        return config

    @classmethod
    def get_label_config(cls, team_id, label):
        config = cls.get_current_config(team_id)
        label_config = config["data"][label]

        if not label_config:
            raise NotFoundError("No config found.")

        return label_config

    @classmethod
    def revert_config(cls, team_id, config_id):
        configs = ConfigController._list(
            filters={"Config": {"team_id": team_id, "id": config_id}}, limit=1
        )
        config = next(iter(configs), None)
        if not config:
            return None

        db.session.add(config)
        config.updated_at = db.func.now()
        db.session.commit()
        return super().resource_to_dict(config)

    @classmethod
    def before_data_load(cls, data):
        config = data.get("data", {})
        config_labels = config.keys()
        team_id = data["team_id"]

        # Check all labels
        for label, data in config.items():

            # QoS based on a rule
            regex = r"^rule.(.+|'.+')$"
            match = re.search(regex, data["qos"])
            if match:
                rule_name = match.group(1)

                # Remove the quote if exists
                if rule_name.startswith("'"):
                    rule_name = rule_name[1:-1]

                # Search if the rule exists
                try:
                    RuleController.get(
                        filters={"Rule": {"name": rule_name, "team_id": team_id}}
                    )
                except NotFoundError:
                    raise NotFoundError(
                        'Rule "{rule}" defined in label "{label}" does not exist'.format(
                            rule=rule_name, label=label
                        )
                    )

            # Operation and Aggregation QOS are based on other labels
            else:
                dependencies = re.search(r"(\[.+\])", data["qos"])
                deps = dependencies.group(1)[1:-1].split(", ")

                # Check if these labels have also been declared
                for dep in deps:
                    if dep not in config_labels:
                        msg = (
                            'Dependency "{dep}" declared in label "{label}" has not '
                            "been declared in the configuration"
                        )
                        raise NotFoundError(msg.format(dep=dep, label=label))

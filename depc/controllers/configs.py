import re

from depc.controllers import Controller, NotFoundError, IntegrityError
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
        team_id = data["team_id"]

        config_context = cls._create_context_from_config(config)

        # Raise IntegrityError or NotFoundError exceptions in case of wrong configuration
        cls._check_config_from_context(config_context, team_id)

    @classmethod
    def _create_context_from_config(cls, config):
        """
        Parses the whole configuration to create a dictionary representing each labels with
        the related downstream compute task and keeps also a record of all labels with the
        compute type (rule, operation, aggregation), the dependencies or the rule name (when applicable).

        Below, an example of the output:

        {'all_labels': {'Apache': {'compute_type': 'rule', 'rule_name': 'Servers'},
                'Filer': {'compute_type': 'rule', 'rule_name': 'Servers'},
                'Offer': {'compute_type': 'aggregation',
                          'dependencies': ['Website']},
                'Website': {'compute_type': 'operation',
                            'dependencies': ['Filer', 'Apache']}},
        'labels_with_downstream': {'Apache': ('Website', 'operation'),
                        'Filer': ('Website', 'operation'),
                        'Website': ('Offer', 'aggregation')}}

        :param config: the dictionary from the JSON User's configuration
        :return: representation of the User's configuration
        """

        config_context = {"labels_with_downstream": {}, "all_labels": {}}
        regex_patterns = {
            "rule": r"^rule.(.+|'.+')$",
            "operation": r"^operation.(ATLEAST|RATIO|AND|OR)\(?[0.|0-9]*\)?(\[[A-Z]+[a-zA-Z0-9]*(, [A-Z]+[a-zA-Z0-9]*)*?\])$",
            "aggregation": r"^aggregation.(AVERAGE|MIN|MAX)\(?\)?(\[[A-Z]+[a-zA-Z0-9]*(, [A-Z]+[a-zA-Z0-9]*)*?\])$",
        }

        # Create the context with each upstream tasks and the downstream task associated
        # The last task (with no downstream) will not be added to config_context['labels_with_downstream']
        for label_name, data in config.items():
            for compute_type, regex in regex_patterns.items():
                match = re.search(regex, data["qos"])
                if match:
                    try:
                        dependencies = match.group(2)[1:-1].split(", ")
                        for dep in dependencies:
                            if dep not in config_context:
                                config_context["labels_with_downstream"][dep] = {}

                            # Save the downstream label and compute type for each dependencies
                            config_context["labels_with_downstream"][dep] = (
                                label_name,
                                compute_type,
                            )

                            config_context["all_labels"][label_name] = {
                                "compute_type": compute_type,
                                "dependencies": dependencies,
                            }
                    except IndexError:
                        # Rule has no dependency
                        rule_name = match.group(1)

                        # Remove the quotes if exist
                        rule_name = (
                            rule_name[1:-1] if rule_name.startswith("'") else rule_name
                        )

                        config_context["all_labels"][label_name] = {
                            "compute_type": compute_type,
                            "rule_name": rule_name,
                        }

                    break

        return config_context

    @classmethod
    def _check_config_from_context(cls, config_context, team_id):
        # To avoid multiple identical calls to the database
        already_checked_rules = set()

        for label_name, meta in config_context["all_labels"].items():
            # This is not possible to schedule an operation or a rule after an aggregation
            # The only task authorized after an aggregation is also another aggregation
            try:
                dstream_label_name, dstream_compute_type = config_context[
                    "labels_with_downstream"
                ][label_name]
                if (
                    config_context["all_labels"][label_name]["compute_type"]
                    == "aggregation"
                    and dstream_compute_type != "aggregation"
                ):
                    raise IntegrityError(
                        'Label "{dstream_label_name}" could not be executed after label "{label_name}"'.format(
                            dstream_label_name=dstream_label_name, label_name=label_name
                        )
                    )
            except KeyError:
                # It happens when the current label has no downstream compute task
                # (not present into config_context['labels_with_downstream'])
                pass

            if (
                meta["compute_type"] == "rule"
                and config_context["all_labels"][label_name]["rule_name"]
                not in already_checked_rules
            ):
                # Search if the rule exists
                rule_name = config_context["all_labels"][label_name]["rule_name"]

                try:
                    RuleController.get(
                        filters={"Rule": {"name": rule_name, "team_id": team_id}}
                    )
                except NotFoundError:
                    raise NotFoundError(
                        'Rule "{rule}" defined in label "{label}" does not exist'.format(
                            rule=rule_name, label=label_name
                        )
                    )
                already_checked_rules.add(rule_name)
            # This is an operation or an aggregation
            elif (
                meta["compute_type"] == "operation"
                or meta["compute_type"] == "aggregation"
            ):
                for dep in meta["dependencies"]:
                    if dep not in config_context["all_labels"].keys():
                        msg = (
                            'Dependency "{dep}" declared in label "{label}" has not '
                            "been declared in the configuration"
                        )
                        raise NotFoundError(msg.format(dep=dep, label=label_name))

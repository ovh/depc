from flask import json
from loguru import logger

from depc.controllers import (
    Controller,
    AlreadyExistError,
    NotFoundError,
    RequirementsNotSatisfiedError,
)
from depc.controllers.checks import CheckController
from depc.extensions import db, redis
from depc.models.checks import Check
from depc.models.rules import Rule
from depc.tasks.rules import execute_async_rule, execute_sync_rule


class BoolsDpsDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if "bools_dps" not in obj:
            return obj
        obj["bools_dps"] = {int(k): v for k, v in obj["bools_dps"].items()}
        return obj


class RuleController(Controller):
    model_cls = Rule

    @classmethod
    def execute(cls, rule_id, sync=False, **kwargs):
        rule = cls._get({"Rule": {"id": rule_id}})

        # If a parameter is changed, we must change the cache key
        parameters = {c.name: c.parameters for c in rule.checks}

        # The same for the variables
        variables = {
            "rule": {v.name: v.value for v in rule.variables},
            "team": {},
            "sources": {},
            "checks": {},
        }

        def _reformat(var):
            return {v.name: v.value for v in var}

        for check in rule.checks:
            variables["checks"][check.name] = _reformat(check.variables)

            # The same source can appear, we add it once
            source = check.source
            if source.name not in variables["sources"]:
                variables["sources"][source.name] = _reformat(source.variables)

            # Every check is owned by the same team
            if not variables["team"]:
                variables["team"] = _reformat(source.team.variables)

        # Get a unique key used for the cache
        kwargs.update({"variables": variables, "parameters": parameters})
        result_key = redis.get_key_name("rule", rule_id, **kwargs)

        if not redis.exists(result_key):
            msg = "[{0}] Launching the rule with arguments : {1}..."
            logger.bind(result_key=result_key).info(msg.format(rule.name, kwargs))
            logger.bind(result_key=result_key).info(
                "[{0}] {1} checks to execute".format(rule.name, len(rule.checks))
            )

            # Synchronous calls : checks are launched sequentially and the
            # result of the rule is directly sent.
            if sync:
                return execute_sync_rule(
                    rule_id=rule_id,
                    rule_checks=[check.id for check in rule.checks],
                    result_key=result_key,
                    kwargs=kwargs,
                )

            # Asynchronous way : returns a result ID. A Celery task execute
            # the rule and the client must poll the /results/<ID> endpoint
            # to have the complete result.
            cls.schedule_task(
                execute_async_rule,
                rule_id=rule_id,
                rule_checks=[check.id for check in rule.checks],
                result_key=result_key,
                kwargs=kwargs,
            )
        else:
            logger.bind(result_key=result_key).warning(
                "Cache already exists for the rule '{0}'".format(rule.name)
            )
            logger.bind(result_key=result_key).debug(
                "The cache has used the following arguments : {0}".format(kwargs)
            )

            if sync:
                result = redis.get(result_key)
                return json.loads(result, cls=BoolsDpsDecoder)

        return result_key

    @classmethod
    def update(cls, data, filters):
        rule_name = cls.get(filters=filters)["name"]

        # Does the rule is used in the configuration
        from ..controllers.configs import ConfigController

        try:
            config = ConfigController.get_current_config(
                team_id=filters["Rule"]["team_id"]
            )

        # There is no config yet
        except NotFoundError:
            return super(RuleController, cls).update(data, filters)

        labels_queries = [c["qos"] for c in config["data"].values()]
        for query in labels_queries:
            if query.startswith("rule"):
                rule = query.split(".")[1]
                if rule_name in rule:
                    msg = (
                        "Rule {0} is used in your configuration, "
                        "please remove it before.".format(rule_name)
                    )
                    raise RequirementsNotSatisfiedError(msg)

        return super(RuleController, cls).update(data, filters)

    @classmethod
    def update_checks(cls, rule_id, checks_id):
        rule = cls._get(filters={"Rule": {"id": rule_id}})

        checks = []
        for check_id in checks_id:
            check = CheckController._get(filters={"Check": {"id": check_id}})
            checks.append(check)

        rule.checks = checks
        db.session.commit()

        return cls.resource_to_dict(rule)

    @classmethod
    def _join_to(cls, query, object_class):
        if object_class == Check:
            return query.join(Rule.checks)
        return super(RuleController, cls)._join_to(query, object_class)

    @classmethod
    def before_data_load(cls, data):
        """Ensure that all checks exist."""
        if "checks" in data:
            for check_id in data["checks"]:
                try:
                    CheckController.get(filters={"Check": {"id": check_id}})
                except NotFoundError:
                    raise NotFoundError("Check {} not found".format(check_id))

            # Transform ID into objects
            data["checks"] = CheckController._list({"Check": {"id": data["checks"]}})

    @classmethod
    def resource_to_dict(cls, obj, blacklist=False):
        d = super().resource_to_dict(obj, blacklist=False)
        d["checks"] = [CheckController.resource_to_dict(c) for c in obj.checks]
        return d

    @classmethod
    def before_delete(cls, obj):
        # Does the rule still have checks
        if obj.checks:
            msg = "Rule {0} contains {1} check{2}, please remove it before.".format(
                obj.name, len(obj.checks), "s" if len(obj.checks) > 1 else ""
            )
            raise RequirementsNotSatisfiedError(msg)

        # Does the rule is used in the configuration
        from ..controllers.configs import ConfigController

        try:
            config = ConfigController.get_current_config(team_id=obj.team.id)

        # There is no config yet
        except NotFoundError:
            return

        labels_queries = [c["qos"] for c in config["data"].values()]
        for query in labels_queries:
            if query.startswith("rule"):
                rule = query.split(".")[1]
                if obj.name in rule:
                    msg = (
                        "Rule {0} is used in your configuration, "
                        "please remove it before.".format(obj.name)
                    )
                    raise RequirementsNotSatisfiedError(msg)

    @classmethod
    def handle_integrity_error(cls, obj, error):
        db.session.rollback()

        # Name already exists for the team
        if Rule.query.filter_by(name=obj.name, team_id=obj.team_id).first():
            raise AlreadyExistError(
                "The rule {name} already exists.", {"name": obj.name}
            )

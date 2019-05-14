import json
import ssl

from flask import current_app as app
from kafka import KafkaProducer

from depc.controllers.sources import SourceController
from depc.controllers.variables import VariableController
from depc.controllers.checks import CheckController
from depc.controllers.rules import RuleController
from depc.controllers.configs import ConfigController
from depc.controllers.teams import TeamController
from depc.controllers import NotFoundError
from depc.templates import Template


def send_to_kafka(topic, data):
    config = app.config.get("KAFKA_CONFIG")
    conf = {
        'bootstrap_servers': config["hosts"],
        'security_protocol': 'SASL_SSL',
        'sasl_mechanism': 'PLAIN',
        'sasl_plain_username': config["username"],
        'sasl_plain_password': config["password"],
        'ssl_context': ssl.SSLContext(ssl.PROTOCOL_SSLv23),
        'ssl_check_hostname': False,
        'client_id': config["client_id"],
        'value_serializer': lambda v: json.dumps(v).encode("utf-8")
    }

    p = KafkaProducer(**conf)
    p.send(topic, data)
    p.flush()


def get_team_configuration(team_id):
    team = TeamController.get(filters={"Team": {"id": team_id}})

    # Populate sources
    sources = {
        str(s.pop("name")): {"plugin": s["plugin"], "configuration": s["configuration"]}
        for s in SourceController.list(
            filters={"Source": {"team_id": team_id}}, with_checks=False
        )
    }

    # Populate rules & checks
    rules = {}
    for rule in RuleController._list(filters={"Rule": {"team_id": team_id}}):
        rules[rule.name] = {}

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

            source = check.source
            if source.name not in variables["sources"]:
                variables["sources"][source.name] = _reformat(source.variables)

            if not variables["team"]:
                variables["team"] = _reformat(source.team.variables)

        for check in rule.checks:
            template = Template(
                check=check,
                context={
                    "name": "$$NAME$$",
                    "start": "$$START$$",
                    "end": "$$END$$",
                    "variables": variables,
                },
            )
            parameters = template.render()
            rules[rule.name][check.name] = {
                "query": parameters["script"] if "script" in parameters else parameters["query"],
                "threshold": parameters["threshold"],
                "source": check.source.name,
                "type": check.type,
            }

    data = {"team": team["name"], "sources": sources, "rules": rules}

    try:
        data["config"] = ConfigController.get_current_config(team_id).get("data")
    except NotFoundError:
        pass

    return data

import json

from airflow.utils.decorators import apply_defaults

from depc.utils.neo4j import is_active_node, get_records
from scheduler.dags.operators import QosOperator


class RuleOperator(QosOperator):
    ui_color = "#d2ead3"

    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(RuleOperator, self).__init__(params, *args, **kwargs)
        self.full_label = "{}_{}".format(self.topic, self.label)
        self.rule_name = params["rule"]

    def execute(self, context):
        from depc.controllers import NotFoundError
        from depc.controllers.rules import RuleController
        from depc.extensions import redis_scheduler as redis
        from depc.utils import get_start_end_ts

        ds = context["ds"]
        start, end = get_start_end_ts(ds)

        with self.app.app_context():

            # Get the nodes for this team and this label
            query = (
                "MATCH(n:{label}) RETURN n AS Node "
                "ORDER BY Node.name "
                "SKIP {skip} LIMIT {limit}"
            )
            query = query.format(
                label=self.full_label, skip=self.skip, limit=int(self.length)
            )

            records = get_records(query)
            nodes = [dict(record.get("Node").items()) for record in records]

            # Remove old nodes
            nodes = [n for n in nodes if is_active_node(start, end, n)]

            # Get the rule associated to the label for this team
            try:
                rule = RuleController.get(
                    filters={"Rule": {"name": self.rule_name, "team_id": self.team_id}}
                )
            except NotFoundError:
                self.log.warning(
                    "[{0}] The label {1} has no associated rule in DEPC".format(
                        self.team_name, self.label
                    )
                )
                return False

            has_qos = False
            for node in nodes:
                result = RuleController.execute(
                    rule_id=rule["id"],
                    sync=True,
                    name=node["name"],
                    start=start,
                    end=end,
                )

                if result["qos"]["qos"] != "unknown":
                    has_qos = True
                    self.log.info(
                        "[{0}/{1}] The QOS of {2} is {3}%".format(
                            self.team_name,
                            self.label,
                            node["name"],
                            result["qos"]["qos"],
                        )
                    )

                    # Saving to Beamium
                    self.write_metric(
                        metric="depc.qos.node",
                        ts=start,
                        value=result["qos"]["qos"],
                        tags={
                            "label": self.label,
                            "name": node["name"],
                            "team": self.team_id,
                        },
                    )

                    # Used for average computing
                    key = "{ds}.{team}.{label}".format(
                        ds=ds, team=self.team_name, label=self.label
                    )
                    redis.zadd(
                        "{}.sorted".format(key), node["name"], result["qos"]["qos"]
                    )

                    # Save information to reuse it later (`bools_dps` is used in
                    # OperationOperator and `qos` is used in AggregationOperator)
                    redis.set(
                        "{}.{}.node".format(key, node["name"]),
                        json.dumps(
                            {
                                "bools_dps": result["qos"]["bools_dps"],
                                "qos": result["qos"]["qos"],
                            }
                        ),
                    )

                else:
                    self.log.warning(
                        "[{0}/{1}] No QOS for {2}".format(
                            self.team_name, self.label, node["name"]
                        )
                    )

                    # Add it in redis to compute some stats in AfterSubdagOperator
                    redis.sadd(
                        "{ds}.{team}.{label}.noqos".format(
                            ds=ds, team=self.team_name, label=self.label
                        ),
                        node["name"],
                    )

            if not has_qos:
                self.log.warning(
                    "[{0}/{1}] No QOS found for any items".format(
                        self.team_name, self.label
                    )
                )

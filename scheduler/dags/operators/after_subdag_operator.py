import time

from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import QosOperator


class AfterSubdagOperator(QosOperator):
    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(AfterSubdagOperator, self).__init__(params, *args, **kwargs)

    def execute(self, context):
        from depc.extensions import redis_scheduler as redis
        from depc.utils import get_start_end_ts

        ds = context["ds"]
        start, end = get_start_end_ts(ds)

        # Get the start_time created in BeforeSubdagOperator
        data = context["task_instance"].xcom_pull(
            task_ids="{0}.before_subdag".format(self.label)
        )

        # Save the time beween the beginning and the end of the subdag
        time_ellapsed = time.time() - data["start_time"]
        self.logger.info(
            "[{team}/{label}] Subdag done in {time} seconds".format(
                team=self.team_name, label=self.label, time=time_ellapsed
            )
        )
        self.write_metric(
            metric="depc.qos.stats",
            ts=start,
            value=time_ellapsed,
            tags={"team": self.team_id, "label": self.label, "type": "time"},
        )

        # Count the nodes without a computed QOS
        noqos_count = redis.scard(
            "{ds}.{team}.{label}.noqos".format(
                ds=ds, team=self.team_name, label=self.label
            )
        )
        self.logger.info(
            "[{team}/{label}] {count} nodes do not have associated QOS".format(
                team=self.team_name, label=self.label, count=noqos_count
            )
        )
        self.write_metric(
            metric="depc.qos.stats",
            ts=start,
            value=noqos_count,
            tags={"team": self.team_id, "label": self.label, "type": "noqos"},
        )

        # Count the nodes with a QOS
        qos_count = data["count"] - noqos_count
        self.logger.info(
            "[{team}/{label}] {count} nodes have a valid QOS".format(
                team=self.team_name, label=self.label, count=qos_count
            )
        )
        self.write_metric(
            metric="depc.qos.stats",
            ts=start,
            value=qos_count,
            tags={"team": self.team_id, "label": self.label, "type": "qos"},
        )

        # Give some nodes without QOS
        if noqos_count:
            noqos_nodes = redis.srandmember(
                "{ds}.{team}.{label}.noqos".format(
                    ds=ds, team=self.team_name, label=self.label
                ),
                10,
            )

            # TODO : we must save it somewhere in order to provide the data to the user
            self.logger.info(
                "[{team}/{label}] Examples of nodes without QOS : {nodes}".format(
                    team=self.team_name, label=self.label, nodes=str(noqos_nodes)
                )
            )

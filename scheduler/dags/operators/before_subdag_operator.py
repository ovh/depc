import time

from airflow.utils.decorators import apply_defaults

from depc.extensions import redis_scheduler as redis
from scheduler.dags.operators import QosOperator


class BeforeSubdagOperator(QosOperator):
    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(BeforeSubdagOperator, self).__init__(params, *args, **kwargs)
        self.count = params["count"]
        self.excluded_nodes_from_average = params["excluded_nodes_from_average"]

    def execute(self, context):
        from depc.utils import get_start_end_ts

        self.logger.info(
            "Excluded nodes for {label}: {excluded}".format(
                label=self.label, excluded=self.excluded_nodes_from_average
            )
        )
        if self.excluded_nodes_from_average:
            redis_key = "{team}.{label}.excluded_nodes_from_label_average".format(
                team=self.team_name, label=self.label
            )
            redis.delete(redis_key)
            redis.rpush(redis_key, *self.excluded_nodes_from_average)

        ds = context["ds"]
        start, end = get_start_end_ts(ds)

        # Save the total number of nodes in this label
        self.logger.info(
            "[{team}/{label}] Label contains {count} nodes".format(
                team=self.team_name, label=self.label, count=self.count
            )
        )
        self.write_metric(
            metric="depc.qos.stats",
            ts=start,
            value=self.count,
            tags={"team": self.team_id, "label": self.label, "type": "total"},
        )

        # We'll use the AfterSubdagOperator to compute
        # some statistics using xcom.
        return {"count": self.count, "start_time": time.time()}

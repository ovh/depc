import time

from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import QosOperator


class BeforeSubdagOperator(QosOperator):
    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(BeforeSubdagOperator, self).__init__(params, *args, **kwargs)
        self.count = params["count"]

    def execute(self, context):
        from depc.utils import get_start_end_ts

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

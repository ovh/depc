import numpy as np
from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import QosOperator


class AverageOperator(QosOperator):
    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(AverageOperator, self).__init__(params, *args, **kwargs)

    def execute(self, context):
        """
        This task computes the average QOS for a label, using a
        special key in Redis populated by the chunks.
        """
        from depc.extensions import redis_scheduler as redis
        from depc.utils import get_start_end_ts

        ds = context["ds"]
        start, end = get_start_end_ts(ds)

        # Get the list of QOS for the label
        key = "{ds}.{team}.{label}.average".format(
            ds=ds, team=self.team_name, label=self.label
        )
        all_qos = [float(qos) for qos in redis.lrange(key, 0, -1)]

        if not all_qos:
            self.log.critical("No QOS found for any {}, aborting.".format(self.label))
            return

        self.log.info(
            "[{0}/{1}] Computing the average QOS using {2} items...".format(
                self.team_name, self.label, len(all_qos)
            )
        )

        # Let's Numpy computes the average
        avg_qos = np.mean(all_qos)

        self.log.info(
            "[{0}/{1}] The average QOS is {2}%".format(
                self.team_name, self.label, avg_qos
            )
        )

        # Saving to Beamium
        self.write_metric(
            metric="depc.qos.label",
            ts=start,
            value=avg_qos,
            tags={"name": self.label, "team": self.team_id},
        )

import time

from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import QosOperator


class DailyWorstOperator(QosOperator):
    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(DailyWorstOperator, self).__init__(params, *args, **kwargs)

    def execute(self, context):
        from depc.controllers import NotFoundError
        from depc.controllers.worst import WorstController
        from depc.models.worst import Periods

        # get the right start and end with the date of the DAG
        ds = context["ds"]

        with self.app.app_context():
            from depc.extensions import redis_scheduler as redis

            key = "{ds}.{team}.{label}.sorted".format(
                ds=ds, team=self.team_name, label=self.label
            )

            start = time.time()
            # E.g.: [(b'filer1', 99), (b'filer3', 99.7), (b'filer2', 99.99)]
            data = redis.zrange(
                key, 0, self.app.config["MAX_WORST_ITEMS"] - 1, withscores=True
            )
            self.log.info(
                "Redis ZRANGE command took {}s".format(round(time.time() - start, 3))
            )

            # produce the data for the relational database
            worst_items = {}
            for node, qos in data:
                if qos < 100:
                    worst_items[node.decode("utf-8")] = qos

            nb_worst_items = len(worst_items)
            if nb_worst_items:
                self.log.info("Worst: {} item(s)".format(nb_worst_items))

                metadata = {
                    "team_id": self.team_id,
                    "label": self.label,
                    "period": Periods.daily,
                    "date": ds,
                }

                try:
                    WorstController.update(
                        data={"data": worst_items}, filters={"Worst": metadata}
                    )
                except NotFoundError:
                    payload = {"data": worst_items}
                    payload.update(metadata)
                    WorstController.create(payload)
            else:
                self.log.info("No QOS under 100%")

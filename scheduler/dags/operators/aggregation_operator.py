from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import DependenciesOperator


class AggregationOperator(DependenciesOperator):
    ui_color = "#c9daf8"

    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(AggregationOperator, self).__init__(params, *args, **kwargs)

    def compute_node_qos(self, data, start, end):
        from depc.utils.qos import AggregationTypes

        # Keep the good values
        data = [d["qos"] for d in data]

        qos = getattr(AggregationTypes, self.type)(data)
        return {"qos": qos}

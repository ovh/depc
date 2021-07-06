import re

from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import DependenciesOperator


class OperationOperator(DependenciesOperator):
    ui_color = "#f4cccc"

    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(OperationOperator, self).__init__(params, *args, **kwargs)

    def compute_node_qos(self, data, start, end):
        from depc.utils.qos import compute_qos_from_bools, check_enable_auto_fill
        from depc.utils.qos import OperationTypes

        # Keep the good values
        data = [d["bools_dps"] for d in data]

        # RATIO and ATLEAST need an argument
        r = re.search(r"(.*)\((.*?)\)", self.type)
        if r:
            type = getattr(OperationTypes, r.group(1))(float(r.group(2)))
        else:
            type = getattr(OperationTypes, self.type)

        with self.app.app_context():
            # At this point, there is no DepC rule to compute the QoS, then
            # the only ID provided is the team ID for check_enable_auto_fill()
            result = compute_qos_from_bools(
                booleans=data,
                start=start,
                end=end,
                agg_op=type,
                auto_fill=check_enable_auto_fill(self.team_id),
            )

        return {"qos": result["qos"], "bools_dps": result["bools_dps"]}

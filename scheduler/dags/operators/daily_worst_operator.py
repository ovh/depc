import time

from airflow.utils.decorators import apply_defaults

from scheduler.dags.operators import QosOperator

MAX_WORST_ITEMS = 15

MAX_DATAPOINTS = 2000000

"""
'{start}' 'start' STORE
'{end}' 'end' STORE
'{token}' 'token' STORE
$token AUTHENTICATE
{max_gts} MAXGTS

"""

WORST_ITEMS_PER_LABEL = """
$COUNT$ 'topN' STORE
$topN 1 - 'topN' STORE

[   $token
    'depc.qos.node'
    { 'team' '$TEAM$' 'label' '$LABEL$' }
    $start $end
] FETCH

// remove useless DATA
{  '.app' '' 'label' '' } RELABEL

// compute mean value over the whole timespan
[ SWAP bucketizer.mean 0 0 1 ] BUCKETIZE

// sort the GTS (based on their latest value)
LASTSORT

// return results if any, else an empty stack []
DUP
SIZE 'topSize' STORE

<% $topSize 0 > %>
<% [ 0 $topN ] SUBLIST %>
IFT
"""


class DailyWorstOperator(QosOperator):
    @apply_defaults
    def __init__(self, params, *args, **kwargs):
        super(DailyWorstOperator, self).__init__(params, *args, **kwargs)

    def execute(self, context):
        from depc.controllers import NotFoundError
        from depc.controllers.worst import WorstController
        from depc.models.worst import Periods
        from depc.utils import get_start_end_ts
        from depc.utils.warp10 import Warp10Client

        # get the right start and end with the date of the DAG
        ds = context["ds"]
        start, end = get_start_end_ts(ds)

        with self.app.app_context():
            client = Warp10Client(use_cache=True)
            client.generate_script(
                WORST_ITEMS_PER_LABEL,
                start,
                end,
                max_gts=MAX_DATAPOINTS,
                extra_params={
                    "team": self.team_id,
                    "label": self.label,
                    "count": str(MAX_WORST_ITEMS),
                },
            )
            start = time.time()
            results = client.execute()
            self.log.info(
                "Warp10 script took {}s".format(round(time.time() - start, 3))
            )

            # produce the data for the relational database
            worst_items = {}
            for d in results[0]:
                qos = d["v"][0][1]
                if qos < 100:
                    worst_items[d["l"]["name"]] = qos

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

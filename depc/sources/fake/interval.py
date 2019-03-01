import logging

import numpy as np

from depc.sources.exceptions import (
    BadConfigurationException,
    DataFetchException,
    UnknownStateException,
)
from depc.sources.fake import Fake, fake_plugin
from depc.sources.utils import compute_interval

logger = logging.getLogger(__name__)


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "metric": {
            "title": "Metric",
            "type": "string",
            "description": "Metric to analyse",
        },
        "bottom_threshold": {
            "title": "Bottom Threshold",
            "type": "number",
            "description": "The QOS will be lowered for every values strictly inferior to this threshold.",
        },
        "top_threshold": {
            "title": "Top Threshold",
            "type": "number",
            "description": "The QOS will be lowered for every values strictly superior to this threshold.",
        },
    },
    "required": ["top_threshold", "bottom_threshold"],
}


FORM = [
    {"key": "metric", "placeholder": "depc.tutorial.httpstatus"},
    {"key": "bottom_threshold", "placeholder": "Ex: 200"},
    {"key": "top_threshold", "placeholder": "Ex: 499"},
]


@fake_plugin.check(schema=SCHEMA, form=FORM)
class IntervalCheck(Fake):
    """
    Every datapoints above a critical threshold lower the QOS.
    """

    name = "Interval"

    @staticmethod
    def _generate_fake_http_status(random_state, size):
        """
        Generate random HTTP Status codes, mostly values will be 200,
        but some of them will be randomly assigned to a 500 during a random range between 1 and 20 ticks,
        or 0 (Curl returned value when Web sites are not reachable)
        """
        values = [200] * size
        picked_error_values_indexes = random_state.choice(
            size, round(0.0015 * len(values)), replace=False
        )
        picked_zero_values_indexes = random_state.choice(
            size, round(0.001 * len(values)), replace=False
        )

        for index in picked_zero_values_indexes:
            values[index] = 0

        for idx in picked_error_values_indexes:
            for i in range(random_state.random_integers(1, 20)):
                try:
                    values[idx + i] = 500
                except IndexError:
                    pass

        return values

    async def execute(self, parameters, name, start, end):
        metric = parameters["metric"]
        start = start.timestamp
        end = end.timestamp

        # Our fake database just provides one metric for the interval check
        if metric != "depc.tutorial.httpstatus":
            raise UnknownStateException("Metric is not available for the tutorial")

        random_state = super().create_random_state(start, end, name)

        # Generate datapoints
        timestamps = list(map(int, np.arange(start, end, 60, dtype=int)))
        values = self._generate_fake_http_status(random_state, len(timestamps))

        dps = dict(zip(timestamps, values))

        timeseries = [{"dps": dps, "metric": metric, "tags": {"name": name}}]

        # Parse the thresholds
        try:
            top_threshold = float(parameters["top_threshold"])
            bottom_threshold = float(parameters["bottom_threshold"])
        except ValueError:
            msg = "Thresholds are not valid (must be floats): {} and {}".format(
                parameters["top_threshold"], parameters["bottom_threshold"]
            )
            raise BadConfigurationException(msg)

        try:
            result = compute_interval(
                timeseries, start, end, bottom_threshold, top_threshold
            )
        except DataFetchException as e:
            raise UnknownStateException(e)

        result.update({"timeseries": timeseries})

        return result

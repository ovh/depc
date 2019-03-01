import logging

import numpy as np

from depc.sources.exceptions import (
    BadConfigurationException,
    DataFetchException,
    UnknownStateException,
)
from depc.sources.fake import Fake, fake_plugin
from depc.sources.utils import compute_threshold

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
        "threshold": {
            "title": "Threshold",
            "type": "number",
            "description": "The QOS will be lowered for every values strictly superior to this threshold.",
        },
    },
    "required": ["metric", "threshold"],
}


FORM = [
    {"key": "metric", "placeholder": "depc.tutorial.ping"},
    {"key": "threshold", "placeholder": "Ex: 20"},
]


@fake_plugin.check(schema=SCHEMA, form=FORM)
class ThresholdCheck(Fake):
    """
    Every datapoints above a critical threshold lower the QOS.
    """

    name = "Threshold"

    @staticmethod
    def _generate_fake_ping_data(random_state, size):
        """
        Generate random ping values (in milliseconds) between 5 and 20,
        some of them will be assigned randomly to a low latency between 100 and 200
        with direct close values between 40 and 80
        """
        values = random_state.random_integers(low=5, high=20, size=size)
        picked_low_latency_values_indexes = random_state.choice(
            size, round(0.001 * len(values)), replace=False
        )

        # Sets the picked value to a random low ping (e.g.: [100, 200]),
        # and sets the direct close values to a ping between 40 and 80ms
        for index in picked_low_latency_values_indexes:
            if index - 1 >= 0:
                values[index - 1] = random_state.random_integers(40, 80)

            values[index] = random_state.random_integers(100, 200)

            if index + 1 < size:
                values[index + 1] = random_state.random_integers(40, 80)

        return values.tolist()

    @staticmethod
    def _generate_fake_oco_status(random_state, size):
        """
        Generate random OCO status, mostly assigned to 200 with some 300 status codes
        during a random range between 4 and 50 ticks
        """
        values = [200] * size
        picked_error_values_indexes = random_state.choice(
            size, round(0.001 * len(values)), replace=False
        )

        for index in picked_error_values_indexes:
            values[index] = 300

            _range = range(random_state.random_integers(0, 50))

            for n in _range:
                position = index + n
                if position < size:
                    values[position] = 300

        return values

    @staticmethod
    def _generate_fake_db_connections(random_state, size):
        """
        Generate random database connections mostly between 10 and 20 occurrences,
        assigned some ticks with a maximum connection pick up to 200
        """
        values = random_state.random_integers(low=10, high=20, size=size)
        picked_max_connections_indexes = random_state.choice(
            size, round(0.005 * len(values)), replace=False
        )

        for index in picked_max_connections_indexes:
            # Creates a linear progression between a healthy state to a bad state
            linear_values = np.arange(20, 210, 10)

            for n in range(len(linear_values) + random_state.random_integers(0, 6)):
                try:
                    if n >= len(linear_values):
                        values[index + n] = 200
                    else:
                        values[index + n] = linear_values[n]
                except IndexError:
                    pass

        return values.tolist()

    async def execute(self, parameters, name, start, end):
        metric = parameters["metric"]
        start = start.timestamp
        end = end.timestamp

        # Our fake database just provides 3 metrics
        random_metrics_dispatcher = {
            "depc.tutorial.ping": self._generate_fake_ping_data,
            "depc.tutorial.oco": self._generate_fake_oco_status,
            "depc.tutorial.dbconnections": self._generate_fake_db_connections,
        }

        if metric not in random_metrics_dispatcher.keys():
            raise UnknownStateException("Metric is not available for the tutorial")

        random_state = super().create_random_state(start, end, name)

        # Generate datapoints
        timestamps = list(map(int, np.arange(start, end, 60, dtype=int)))
        values = random_metrics_dispatcher[metric](random_state, len(timestamps))
        dps = dict(zip(timestamps, values))

        timeseries = [{"dps": dps, "metric": metric, "tags": {"name": name}}]

        # Parse the threshold
        try:
            threshold = float(parameters["threshold"])
        except ValueError:
            msg = "Threshold is not valid (must be float): {}".format(
                parameters["threshold"]
            )
            raise BadConfigurationException(msg)

        try:
            result = compute_threshold(timeseries, start, end, threshold)
        except DataFetchException as e:
            raise UnknownStateException(e)

        result.update({"timeseries": timeseries})

        return result

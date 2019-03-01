import json
import logging
from json.decoder import JSONDecodeError

from depc.sources.exceptions import (
    BadConfigurationException,
    DataFetchException,
    UnknownStateException,
)
from depc.sources.opentsdb import OpenTSDB, opentsdb_plugin
from depc.sources.utils import compute_threshold

logger = logging.getLogger(__name__)


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "query": {
            "title": "OpenTSDB query",
            "type": "string",
            "description": "Query must return 1 or more timeserie(s).",
        },
        "threshold": {
            "title": "Threshold",
            "type": "string",
            "description": "The QOS will be lowered for every values strictly superior to this threshold.",
        },
    },
    "required": ["query", "threshold"],
}


FORM = [
    {"key": "query", "type": "codemirror"},
    {"key": "threshold", "placeholder": "Ex: 500"},
]


@opentsdb_plugin.check(schema=SCHEMA, form=FORM)
class ThresholdCheck(OpenTSDB):
    """
    This check executes a query on an OpenTSDB : every datapoints which
    is above a critical threshold lower the QOS.
    """

    name = "Threshold"

    async def compute(self, parameters, name, start, end, query):
        logger.debug("Computing the QoS in {0} check".format(self.name))

        timeseries = await self.make_query(query)
        if not timeseries:
            msg = "No data for {} (from {} to {})".format(name, start, end)
            logger.warning(msg)
            raise UnknownStateException(msg)

        # Parse the threshold
        try:
            threshold = float(parameters["threshold"])
        except ValueError:
            msg = "Threshold is not valid (must be float): {}".format(
                parameters["threshold"]
            )
            raise BadConfigurationException(msg)

        # Compute the QoS
        try:
            result = compute_threshold(
                timeseries, start.timestamp, end.timestamp, threshold
            )
        except DataFetchException as e:
            raise UnknownStateException(e)

        result.update({"timeseries": timeseries})

        return result

    async def execute(self, parameters, name, start, end):
        try:
            query = {
                "start": start.timestamp,
                "end": end.timestamp,
                "queries": [json.loads(parameters["query"])],
            }
        except JSONDecodeError as e:
            raise BadConfigurationException(
                "Json Error in OpenTSDB query : {0}".format(str(e))
            )
        except ValueError:
            msg = "OpenTSDB Query is not valid : {}".format(parameters["query"])
            raise BadConfigurationException(msg)

        return await self.compute(parameters, name, start, end, query)

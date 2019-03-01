import json
import logging
from json.decoder import JSONDecodeError

from depc.sources.exceptions import (
    BadConfigurationException,
    DataFetchException,
    UnknownStateException,
)
from depc.sources.opentsdb import OpenTSDB, opentsdb_plugin
from depc.sources.utils import compute_interval

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
        "bottom_threshold": {
            "title": "Bottom Threshold",
            "type": "string",
            "description": "The QOS will be lowered for every values strictly inferior to this threshold.",
        },
        "top_threshold": {
            "title": "Top Threshold",
            "type": "string",
            "description": "The QOS will be lowered for every values strictly superior to this threshold.",
        },
    },
    "required": ["query", "top_threshold", "bottom_threshold"],
}


FORM = [
    {"key": "query", "type": "codemirror"},
    {"key": "bottom_threshold", "placeholder": "Ex: -200"},
    {"key": "top_threshold", "placeholder": "Ex: 200"},
]


@opentsdb_plugin.check(schema=SCHEMA, form=FORM)
class IntervalCheck(OpenTSDB):
    """
    This check executes a query on an OpenTSDB : every datapoints which
    are outside a given interval lower the QOS.
    """

    name = "Interval"

    async def compute(self, parameters, name, start, end, query):
        logger.debug("Computing the QoS in {0} check".format(self.name))

        timeseries = await self.make_query(query)
        if not timeseries:
            msg = "No data for {} (from {} to {})".format(name, start, end)
            logger.warning(msg)
            raise UnknownStateException(msg)

        # Parse the threshold
        try:
            top_threshold = float(parameters["top_threshold"])
            bottom_threshold = float(parameters["bottom_threshold"])
        except ValueError:
            msg = "Thresholds are not valid (must be floats): {} and {}".format(
                parameters["top_threshold"], parameters["bottom_threshold"]
            )
            raise BadConfigurationException(msg)

        # Compute the QoS
        try:
            result = compute_interval(
                timeseries,
                start.timestamp,
                end.timestamp,
                bottom_threshold,
                top_threshold,
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

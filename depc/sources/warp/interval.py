import html
import logging
import re

from depc.sources.exceptions import (
    BadConfigurationException,
    DataFetchException,
    UnknownStateException,
)
from depc.sources.utils import compute_interval
from depc.sources.warp import Warp10, warp_plugin
from depc.utils.warp10 import Warp10Client, Warp10Exception, _transform_warp10_values

logger = logging.getLogger(__name__)


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "script": {
            "title": "WarpScript",
            "type": "string",
            "description": "Script must return 1 or more timeserie(s).",
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
    "required": ["script", "top_threshold", "bottom_threshold"],
}


FORM = [
    {"key": "script", "type": "codemirror"},
    {"key": "bottom_threshold", "placeholder": "Ex: -200"},
    {"key": "top_threshold", "placeholder": "Ex: 200"},
]


@warp_plugin.check(schema=SCHEMA, form=FORM)
class IntervalCheck(Warp10):
    """
    This check launches a script on a Warp10 platform : every datapoints which
    are outside a given interval lower the QOS.
    """

    name = "Interval"

    async def execute(self, parameters, name, start, end):
        client = Warp10Client(
            url=self.configuration["url"], rotoken=self.configuration["token"]
        )

        # Generate the WarpScript and
        # change the placeholders.
        client.generate_script(
            start=start.timestamp, end=end.timestamp, script=parameters["script"]
        )

        try:
            response = await client.async_execute()
        except Warp10Exception as e:
            try:
                message = html.unescape(
                    re.search("<pre>(.*)<\/pre>", str(e)).groups()[0].strip()
                )
            except Exception:
                message = str(e)
            raise BadConfigurationException(
                "Warp10 Internal Error : {0}".format(message)
            )

        # Transform the Warp10 values
        timeseries = []
        try:
            for ts in response[0]:
                timeseries.append(
                    {
                        "dps": _transform_warp10_values(ts["v"]),
                        "metric": ts["c"],
                        "tags": ts["l"],
                    }
                )

        # Response is not parsable, return it to the user for debugging
        except TypeError:
            raise BadConfigurationException(
                "Script does not return valid format : {}".format(response)
            )

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

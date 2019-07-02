import html
import logging
import re

from depc.sources import BaseSource, SourceRegister
from depc.sources.exceptions import BadConfigurationException
from depc.utils.warp10 import Warp10Client, Warp10Exception, _transform_warp10_values

logger = logging.getLogger(__name__)
warp_plugin = SourceRegister()


SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "title": "Url",
            "type": "string",
            "description": "The url used to launch the scripts.",
        },
        "token": {
            "title": "Token",
            "type": "string",
            "description": "A read only token used authenticate the scripts.",
        },
    },
    "required": ["url", "token"],
}


FORM = [
    {"key": "url", "placeholder": "http://127.0.0.1"},
    {"key": "token", "placeholder": "foobar"},
]


@warp_plugin.source(schema=SCHEMA, form=FORM)
class Warp10(BaseSource):
    """
    Use a database Warp10 to launch your WarpScripts.
    """

    name = "WarpScript"

    async def execute(self, parameters, name, start, end):
        client = Warp10Client(
            url=self.configuration["url"], rotoken=self.configuration["token"]
        )

        # Generate the WarpScript and change the placeholders
        client.generate_script(start=start, end=end, script=parameters["query"])

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

        return timeseries

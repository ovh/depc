import json
import logging
from json.decoder import JSONDecodeError

import aiohttp

from depc.sources import BaseSource, SourceRegister
from depc.sources.exceptions import BadConfigurationException, DataFetchException


logger = logging.getLogger(__name__)
opentsdb_plugin = SourceRegister()


SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "title": "Url",
            "type": "string",
            "description": "The url used to query the database.",
        },
        "credentials": {
            "title": "Credentials",
            "type": "string",
            "description": "The credentials used authenticate the queries.",
        },
    },
    "required": ["url", "credentials"],
}


FORM = [
    {"key": "url", "placeholder": "http://127.0.0.1"},
    {"key": "credentials", "placeholder": "foo:bar"},
]


@opentsdb_plugin.source(schema=SCHEMA, form=FORM)
class OpenTSDB(BaseSource):
    """
    Use an OpenTSDB database to launch your queries.
    """

    name = "OpenTSDB"

    def build_query(self, name, start, end, parameters):
        try:
            query = {
                "start": int(start) - 1,
                "end": int(end),
                "queries": [json.loads(parameters["query"])],
            }
        except JSONDecodeError as e:
            raise BadConfigurationException(
                "Json Error in OpenTSDB query : {0}".format(str(e))
            )
        except ValueError:
            msg = "OpenTSDB Query is not valid : {}".format(parameters["query"])
            raise BadConfigurationException(msg)

        return query

    async def execute(self, parameters, name, start, end):
        query = self.build_query(name, start, end, parameters)

        url = self.configuration["url"] + "/api/query"
        credentials = self.configuration["credentials"].split(":", maxsplit=1)

        auth = aiohttp.BasicAuth(credentials[0], credentials[1])
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(url, json=query) as r:
                if r.status != 200:
                    raise DataFetchException(str(r.text))
                result = await r.json()

        # Convert the query result to be compliant with the Pandas compute
        timeseries = []
        for ts in result:
            timeseries.append(
                {
                    "metric": ts["metric"],
                    "tags": ts["tags"],
                    "dps": {int(k): v for k, v in ts["dps"].items()},
                }
            )

        return timeseries

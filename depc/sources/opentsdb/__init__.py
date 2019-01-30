import json
import logging

import requests

from depc.sources import BaseSource, SourceRegister
from depc.sources.exceptions import DataFetchException

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

    def make_query(self, data):
        url = self.configuration["url"] + "/api/query"

        r = requests.post(
            url,
            auth=tuple(self.configuration["credentials"].split(":", maxsplit=1)),
            data=json.dumps(data),
        )

        if r.status_code != 200:
            raise DataFetchException(str(r.text))
        result = r.json()

        # Convert the query result to be
        # compliant with the Pandas compute
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

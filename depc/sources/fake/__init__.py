import hashlib
import logging

import numpy as np

from depc.sources import BaseSource, SourceRegister
from depc.sources.exceptions import BadConfigurationException
from depc.sources.fake.metrics import (
    generate_fake_db_connections,
    generate_fake_http_status,
    generate_fake_oco_status,
    generate_fake_ping_data,
)

logger = logging.getLogger(__name__)
fake_plugin = SourceRegister()


SCHEMA = {"type": "object", "properties": {}}
FORM = []


@fake_plugin.source(schema=SCHEMA, form=FORM)
class Fake(BaseSource):
    """
    Fake source used in the documentation tutorial.
    """

    name = "Fake"

    @classmethod
    def create_random_state(cls, start, end, name):
        """
        Give a unique seed based on parameters
        """
        slug = "{0}-{1}-{2}".format(start, end, name)
        seed = int(hashlib.sha1(slug.encode("utf-8")).hexdigest()[:7], 16)
        random_state = np.random.RandomState(seed)
        return random_state

    async def execute(self, parameters, name, start, end):
        metric = parameters["query"]

        # Our fake database just provides 4 metrics
        random_metrics_dispatcher = {
            "depc.tutorial.ping": generate_fake_ping_data,
            "depc.tutorial.oco": generate_fake_oco_status,
            "depc.tutorial.dbconnections": generate_fake_db_connections,
            "depc.tutorial.httpstatus": generate_fake_http_status,
        }

        if metric not in random_metrics_dispatcher.keys():
            raise BadConfigurationException("Metric is not available for the tutorial")

        # Generate datapoints
        random_state = self.create_random_state(start, end, name)
        timestamps = list(map(int, np.arange(start, end, 60, dtype=int)))
        values = random_metrics_dispatcher[metric](random_state, len(timestamps))
        dps = dict(zip(timestamps, values))

        return [{"dps": dps, "metric": metric, "tags": {"name": name}}]

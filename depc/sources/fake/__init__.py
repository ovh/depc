import hashlib
import logging

import numpy as np

from depc.sources import BaseSource, SourceRegister

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

    def make_query(self, data):
        pass

    @staticmethod
    def create_random_state(start, end, name):
        """
        Give a unique seed based on parameters
        """
        slug = "{0}-{1}-{2}".format(start, end, name)
        seed = int(hashlib.sha1(slug.encode("utf-8")).hexdigest()[:7], 16)
        random_state = np.random.RandomState(seed)
        return random_state

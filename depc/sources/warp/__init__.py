import logging

from depc.sources import BaseSource, SourceRegister
from depc.sources.exceptions import DataFetchException

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

    @staticmethod
    def transform_values():
        pass

    @staticmethod
    def get_single_value(result):
        try:
            if len(result) > 1:
                raise DataFetchException(
                    "Single value was expected, multiple were found"
                )
            value = result[0]
            try:
                value = float(value)
            except TypeError:
                raise DataFetchException("Qos must be a float value")
            return value
        except LookupError:
            raise DataFetchException("No result from data fetch")

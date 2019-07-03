import textwrap

from jsonschema import validate
import pandas as pd

from depc.sources.exceptions import BadConfigurationException
from depc.utils.qos import compute_qos_from_bools


def validate_config(config_schema, config):
    validate(config, config_schema)


class SourceRegister(object):

    sources = {}

    def __init__(self):
        self.name = None
        self.source_cls = None

    def source(self, **options):
        def decorator(source):
            self.sources[source.name] = {
                "source_cls": source,
                "schema": options.pop("schema", {}),
                "form": options.pop("form", {}),
            }
            return source

        return decorator

    @classmethod
    def get_source(cls, name):
        try:
            return cls.sources[name]
        except KeyError:
            return None


class BaseSource(object):
    def __init__(self, config):
        self.configuration = config

    @classmethod
    def load_source(cls, source_name, config):
        source = cls._get_source(source_name)
        return source["source_cls"](config)

    @classmethod
    def validate_source_config(cls, source_name, config):
        source = cls._get_source(source_name)
        return validate(config, source["schema"])

    @classmethod
    def _get_source(cls, source_name):
        source = SourceRegister.get_source(source_name)
        if not source:
            raise NotImplementedError("Source %s is undefined" % source_name)
        return source

    @classmethod
    def format_source(cls, source):
        return {
            "description": textwrap.dedent(source["source_cls"].__doc__).strip(),
            "schema": source["schema"],
            "form": source["form"],
        }

    @classmethod
    def available_sources(cls):
        sources = []
        for source, data in SourceRegister.sources.items():
            sources.append({"name": source, **cls.format_source(data)})
        return sources

    @classmethod
    def source_information(cls, source_name):
        source = cls._get_source(source_name)
        return cls.format_source(source)

    @classmethod
    def is_float(cls, threshold):
        try:
            float(threshold)
        except ValueError:
            return False
        return True

    @classmethod
    def is_threshold(cls, threshold):
        return cls.is_float(threshold)

    @classmethod
    def is_interval(cls, threshold):
        return (
            len(threshold.split(":")) == 2
            and cls.is_float(threshold.split(":")[0])
            and cls.is_float(threshold.split(":")[1])
        )

    async def execute(self, parameters, name, start, end):
        raise NotImplementedError

    async def run(self, parameters, name, start, end):
        timeseries = await self.execute(parameters, name, start, end)
        threshold = parameters["threshold"]

        # Handle a simple threshold
        if self.is_threshold(parameters["threshold"]):
            threshold = float(threshold)
            bool_per_ts = [
                pd.Series(ts["dps"]).apply(lambda x: x <= threshold)
                for ts in timeseries
            ]

        # Handle an interval
        elif self.is_interval(parameters["threshold"]):
            bottom = float(threshold.split(":")[0])
            top = float(threshold.split(":")[1])
            bool_per_ts = [
                pd.Series(ts["dps"]).apply(lambda x: bottom <= x <= top)
                for ts in timeseries
            ]
        else:
            raise BadConfigurationException(
                "Bad threshold format : {}".format(parameters["threshold"])
            )

        result = compute_qos_from_bools(bool_per_ts, start, end)
        result.update({"timeseries": timeseries})

        return result

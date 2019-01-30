import copy
import textwrap

import arrow
from jsonschema import validate


def validate_config(config_schema, config):
    validate(config, config_schema)


class SourceRegister(object):

    sources = {}

    def __init__(self):
        self.name = None
        self.source_cls = None
        self.configuration_model = {}
        self.checks = {}

    def source(self, **options):
        def decorator(source):
            self.sources[source.name] = {
                "source_cls": source,
                "schema": options.pop("schema", {}),
                "form": options.pop("form", {}),
                "checks": self.checks,
            }
            return source

        return decorator

    def check(self, **options):
        def decoractor(check):
            self.checks[check.name] = {
                "check_cls": check,
                "schema": options.pop("schema", {}),
                "form": options.pop("form", {}),
            }
            return check

        return decoractor

    @classmethod
    def get_source(cls, name):
        try:
            return cls.sources[name]
        except KeyError:
            return None

    @classmethod
    def get_check(cls, source_name, check_name):
        source = cls.get_source(source_name)
        try:
            return source["checks"][check_name]
        except KeyError:
            return None


class Check(object):
    def __init__(self, source, check_cls, parameters, name, start, end):
        self.source = source
        self.check_cls = check_cls
        self.parameters = parameters
        self.name = name
        self.start = arrow.get(start)
        self.end = arrow.get(end)

    def execute(self):
        check = self.check_cls(config=self.source.configuration)

        return check.execute(self.parameters, self.name, self.start, self.end)


class BaseSource(object):
    def __init__(self, config):
        self.configuration = config

    @classmethod
    def load_source(cls, source_name, config):
        source = cls._get_source(source_name)
        return source["source_cls"](config)

    def load_check(self, check_name, parameters, name, start, end):
        check = self._get_check(check_name)
        return Check(self, check["check_cls"], parameters, name, start, end)

    @classmethod
    def validate_source_config(cls, source_name, config):
        source = cls._get_source(source_name)
        return validate(config, source["schema"])

    @classmethod
    def validate_check_parameters(cls, check_name, parameters):
        check = cls._get_check(check_name)
        schema = copy.deepcopy(check["schema"])

        # Check 'object' key to convert all strings to object
        for field in check["form"]:
            if "object" in field and field["object"] is True:
                schema["properties"][field["key"]]["type"] = "object"

        return validate(parameters, schema)

    @classmethod
    def _get_check(cls, check_name):
        check = SourceRegister.get_check(cls.name, check_name)
        if not check:
            raise NotImplementedError(
                "Check %s is not supported for source %s" % (check_name, cls.name)
            )
        return check

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
    def format_check(cls, check):
        return {
            "description": textwrap.dedent(check["check_cls"].__doc__).strip(),
            "schema": check["schema"],
            "form": check["form"],
        }

    @classmethod
    def available_checks(cls, source_name):
        source = cls._get_source(source_name)
        checks = []

        for name, check in source["checks"].items():
            checks.append({"name": name, **cls.format_check(check)})

        return checks

    @classmethod
    def check_information(cls, source_name, check_name):
        source = cls._get_source(source_name)
        check = source["source_cls"]._get_check(check_name)
        return cls.format_check(check)

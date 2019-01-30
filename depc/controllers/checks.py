from depc.controllers import Controller, NotFoundError
from depc.controllers.sources import SourceController
from depc.models.checks import Check
from depc.models.rules import Rule
from depc.sources import BaseSource


class CheckController(Controller):

    model_cls = Check

    @classmethod
    def _join_to(cls, query, object_class):
        if object_class == Rule:
            return query.join(Check.rules)
        return super(CheckController, cls)._join_to(query, object_class)

    @classmethod
    def before_data_load(cls, data):
        """Ensure that the source and checks exist."""
        if "source_id" in data:
            try:
                source = SourceController.get(
                    filters={"Source": {"id": data["source_id"]}}
                )
            except NotFoundError:
                raise NotFoundError("Source {} not found".format(data["source_id"]))

            plugin = BaseSource.load_source(source["plugin"], {})
            plugin.validate_check_parameters(data["type"], data["parameters"])

    @classmethod
    def ensure_check(cls, obj):
        """Ensure check-source compatibility and validate configuration"""
        source = SourceController.get(filters={"Source": {"id": obj.source_id}})
        plugin = BaseSource.load_source(source["plugin"], {})
        plugin.validate_check_parameters(obj.type, obj.parameters)

    @classmethod
    def before_create(cls, obj):
        cls.ensure_check(obj)

    @classmethod
    def before_update(cls, obj):
        cls.ensure_check(obj)

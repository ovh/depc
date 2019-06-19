from depc.controllers import (
    Controller,
    NotFoundError,
    AlreadyExistError,
    IntegrityError,
)
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
        name = obj.name

        # Name surrounded by quotes are prohibited
        if name.startswith(('"', "'")) or name.endswith(('"', "'")):
            raise IntegrityError("The check name cannot begin or end with a quote")

        checks = cls._list(filters={"Check": {"name": name}})
        source = SourceController._get(filters={"Source": {"id": obj.source_id}})

        for check in checks:
            if check.id != obj.id and check.source.team_id == source.team_id:
                raise AlreadyExistError(
                    "The check {name} already exists.", {"name": name}
                )

        plugin = BaseSource.load_source(source.plugin, {})
        plugin.validate_check_parameters(obj.type, obj.parameters)

    @classmethod
    def before_create(cls, obj):
        cls.ensure_check(obj)

    @classmethod
    def before_update(cls, obj):
        cls.ensure_check(obj)

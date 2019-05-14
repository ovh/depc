from flask_login import current_user

from depc.controllers import Controller, RequirementsNotSatisfiedError
from depc.models.sources import Source
from depc.sources import BaseSource


class SourceController(Controller):

    model_cls = Source

    @classmethod
    def list(
        cls,
        filters=None,
        order_by=None,
        limit=None,
        reverse=None,
        blacklist=False,
        with_checks=True,
    ):
        objs = cls._list(filters, order_by, limit, reverse, blacklist)
        return [
            cls.resource_to_dict(o, blacklist=blacklist, with_checks=with_checks)
            for o in objs
        ]

    @classmethod
    def resource_to_dict(cls, obj, blacklist=False, with_checks=True):
        from ..controllers.checks import CheckController

        d = super().resource_to_dict(obj, blacklist=blacklist)
        if with_checks:
            d["checks"] = [CheckController.resource_to_dict(c) for c in obj.checks]
        return d

    @classmethod
    def ensure_plugin(cls, obj):
        BaseSource.validate_source_config(obj.plugin, obj.configuration)

    @classmethod
    def before_create(cls, obj):
        obj.manager = current_user
        cls.ensure_plugin(obj)

    @classmethod
    def before_update(cls, obj):
        cls.ensure_plugin(obj)

    @classmethod
    def before_delete(cls, obj):
        if obj.checks:
            msg = "Source {0} contains {1} check{2}, please remove it before.".format(
                obj.name, len(obj.checks), "s" if len(obj.checks) > 1 else ""
            )
            raise RequirementsNotSatisfiedError(msg)

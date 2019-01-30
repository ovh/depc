from depc.controllers import Controller, NotFoundError
from depc.models.sources import Source
from depc.models.teams import Team
from depc.models.variables import Variable


class VariableController(Controller):

    model_cls = Variable

    @classmethod
    def _join_to(cls, query, object_class):
        if object_class == Source:
            return query.join(Source.variables)
        if object_class == Team:
            return query.join(Team.variables)
        return super(VariableController, cls)._join_to(query, object_class)

    @classmethod
    def _not_found(cls):
        raise NotFoundError("Could not find resource")

    @classmethod
    def _check_object(cls, obj):
        from ..controllers.checks import CheckController
        from ..controllers.rules import RuleController
        from ..controllers.sources import SourceController

        # Team id is always mandatory
        team_id = obj.team_id

        # Check the rule
        if obj.rule_id:
            rule = RuleController.get(
                filters={"Rule": {"id": obj.rule_id, "team_id": team_id}}
            )
            if not rule:
                cls._not_found()

        # Check the source
        if obj.source_id:
            source = SourceController.get(
                filters={"Source": {"id": obj.source_id, "team_id": team_id}}
            )
            if not source:
                cls._not_found()

        # Check the check (haha!)
        if obj.source_id and obj.check_id:
            source = CheckController.get(
                filters={"Check": {"id": obj.check_id, "source_id": obj.source_id}}
            )
            if not source:
                cls._not_found()

    @classmethod
    def resource_to_dict(cls, obj, blacklist=False):
        d = super().resource_to_dict(obj, blacklist=False)
        d["expression"] = obj.expression
        return d

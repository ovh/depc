from depc.controllers import (
    Controller,
    NotFoundError,
    AlreadyExistError,
    IntegrityError,
)
from depc.controllers.sources import SourceController
from depc.extensions import db
from depc.models.checks import Check
from depc.models.rules import Rule
from depc.models.sources import Source
from depc.models.teams import Team


class CheckController(Controller):

    model_cls = Check

    @classmethod
    def list_team_checks(cls, team_id):
        from depc.controllers.teams import TeamController

        _ = TeamController.get({"Team": {"id": team_id}})

        checks = (
            db.session.query(Check)
            .join(Source, Source.id == Check.source_id)
            .join(Team, Team.id == Source.team_id)
            .filter(Team.id == team_id)
            .all()
        )
        return [cls.resource_to_dict(c) for c in checks]

    @classmethod
    def _join_to(cls, query, object_class):
        if object_class == Rule:
            return query.join(Check.rules)
        return super(CheckController, cls)._join_to(query, object_class)

    @classmethod
    def before_data_load(cls, data):
        if "source_id" in data:
            try:
                SourceController.get(filters={"Source": {"id": data["source_id"]}})
            except NotFoundError:
                raise NotFoundError("Source {} not found".format(data["source_id"]))

    @classmethod
    def ensure_check(cls, obj):
        name = obj.name

        # Name surrounded by quotes are prohibited
        if name.startswith(('"', "'")) or name.endswith(('"', "'")):
            raise IntegrityError("The check name cannot begin or end with a quote")

        # Ensure that the check does not exist in another source
        checks = cls._list(filters={"Check": {"name": name}})
        source = SourceController._get(filters={"Source": {"id": obj.source_id}})

        for check in checks:
            if check.id != obj.id and check.source.team_id == source.team_id:
                raise AlreadyExistError(
                    "The check {name} already exists.", {"name": name}
                )

        # Ensure the type field
        if ":" in obj.parameters["threshold"] and obj.type != "Interval":
            raise IntegrityError(
                "Threshold {} must be flagged as interval".format(
                    obj.parameters["threshold"]
                )
            )

    @classmethod
    def before_create(cls, obj):
        cls.ensure_check(obj)

    @classmethod
    def before_update(cls, obj):
        cls.ensure_check(obj)

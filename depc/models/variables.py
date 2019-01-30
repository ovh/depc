from sqlalchemy_utils import UUIDType

from depc.extensions import db
from depc.models import BaseModel


class Variable(BaseModel):

    __tablename__ = "variables"
    __repr_fields__ = ("name", "value", "type")

    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.String(), nullable=False)
    type = db.Column(db.String(255), nullable=False)

    rule_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("rules.id"), nullable=True
    )
    team_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("teams.id"), nullable=False
    )
    source_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("sources.id"), nullable=True
    )
    check_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("checks.id"), nullable=True
    )

    @property
    def level(self):
        if self.check_id:
            return "check"
        elif self.source_id:
            return "source"
        elif self.rule_id:
            return "rule"
        else:
            return "team"

    @property
    def expression(self):
        exp = "depc.{level}['{name}']" if " " in self.name else "depc.{level}.{name}"
        return exp.format(level=self.level, name=self.name)

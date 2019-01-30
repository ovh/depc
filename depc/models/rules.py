from sqlalchemy.schema import UniqueConstraint
from sqlalchemy_utils import UUIDType

from depc.extensions import db
from depc.models import BaseModel

rule_check_association_table = db.Table(
    "rule_check_association",
    db.Column(
        "rule_id", UUIDType(binary=False), db.ForeignKey("rules.id"), primary_key=True
    ),
    db.Column(
        "check_id", UUIDType(binary=False), db.ForeignKey("checks.id"), primary_key=True
    ),
    UniqueConstraint("rule_id", "check_id", name="rule_check_uix"),
)


class Rule(BaseModel):

    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("team_id", "name", name="team_rule_uc"),)
    __repr_fields__ = ("name",)

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(), nullable=True)
    checks = db.relationship(
        "Check",
        backref=db.backref("rules", uselist=True),
        secondary="rule_check_association",
    )

    team_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("teams.id"), nullable=True
    )
    team = db.relationship("Team", back_populates="rules")

    variables = db.relationship(
        "Variable",
        primaryjoin="and_(Rule.id==Variable.rule_id, "
        "Variable.source_id==None, "
        "Variable.check_id==None)",
        backref="rule",
    )

    @property
    def recursive_variables(self):
        variables = {
            "rule": {v.name: v.value for v in self.variables},
            "team": {},
            "sources": {},
            "checks": {},
        }

        def _reformat(var):
            return {v.name: v.value for v in var}

        for check in self.checks:
            variables["checks"][check.name] = _reformat(check.variables)

            # The same source can appear, we add it once
            source = check.source
            if source.name not in variables["sources"]:
                variables["sources"][source.name] = _reformat(source.variables)

            # Every check is owned by the same team
            if not variables["team"]:
                variables["team"] = _reformat(source.team.variables)

        return variables

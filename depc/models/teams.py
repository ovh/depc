from sqlalchemy.ext.associationproxy import association_proxy

from depc.extensions import db
from depc.extensions.encrypted_dict import EncryptedDict
from depc.models import BaseModel


class Team(BaseModel):

    __tablename__ = "teams"
    __repr_fields__ = ("name",)

    name = db.Column(db.String(255), nullable=False)
    sources = db.relationship("Source", back_populates="team")
    rules = db.relationship("Rule", back_populates="team")
    configs = db.relationship("Config", back_populates="team")
    worst = db.relationship("Worst", back_populates="team")

    grants = association_proxy("grants", "user")
    variables = db.relationship(
        "Variable",
        primaryjoin="and_(Team.id==Variable.team_id, "
        "Variable.rule_id==None, "
        "Variable.source_id==None, "
        "Variable.check_id==None)",
        backref="team",
    )
    metas = db.Column(EncryptedDict, default={}, nullable=True)

    @property
    def members(self):
        return [grant.user for grant in self.grants if grant.role.value == "member"]

    @property
    def editors(self):
        return [grant.user for grant in self.grants if grant.role.value == "editor"]

    @property
    def managers(self):
        return [grant.user for grant in self.grants if grant.role.value == "manager"]

    @property
    def kafka_topic(self):
        return "".join(e for e in self.name if e.isalnum()).lower()

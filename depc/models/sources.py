from sqlalchemy_utils import UUIDType

from depc.extensions import db
from depc.extensions.encrypted_dict import EncryptedDict
from depc.models import BaseModel


class Source(BaseModel):

    __tablename__ = "sources"
    __repr_fields__ = ("name", "plugin")

    name = db.Column(db.String(255), nullable=False)

    plugin = db.Column(db.String(255), nullable=False)
    configuration = db.Column(EncryptedDict, default={}, nullable=True)

    checks = db.relationship("Check", back_populates="source")

    team_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("teams.id"), nullable=True
    )
    team = db.relationship("Team", back_populates="sources")

    variables = db.relationship(
        "Variable",
        primaryjoin="and_(Source.id==Variable.source_id, "
        "Variable.rule_id==None, "
        "Variable.check_id==None)",
        backref="source",
    )

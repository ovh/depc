from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils import UUIDType, JSONType

from depc.extensions import db
from depc.models import BaseModel


class Config(BaseModel):

    __tablename__ = "configs"
    __repr_fields__ = ("id", "team")

    team_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("teams.id"), nullable=False
    )
    team = db.relationship("Team", back_populates="configs")

    data = db.Column(MutableDict.as_mutable(JSONType), default={}, nullable=False)

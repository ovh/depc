from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy_utils import UUIDType, JSONType

from depc.extensions import db
from depc.models import BaseModel


class Check(BaseModel):

    __tablename__ = "checks"
    __repr_fields__ = ("name",)

    name = db.Column(db.String(255), nullable=False)

    source_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("sources.id"), nullable=False
    )
    source = db.relationship(
        "Source", backref=db.backref("source_checks", uselist=True)
    )

    type = db.Column(db.String(255), nullable=False)
    parameters = db.Column(MutableDict.as_mutable(JSONType), default={}, nullable=True)

    variables = db.relationship("Variable", backref="check")

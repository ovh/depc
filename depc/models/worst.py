import enum

from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy_utils import UUIDType, JSONType

from depc.extensions import db
from depc.models import BaseModel


class Periods(enum.Enum):
    daily = "daily"
    monthly = "monthly"


class Worst(BaseModel):

    __tablename__ = "worst"
    __table_args__ = (
        UniqueConstraint(
            "team_id", "label", "date", "period", name="team_label_date_period_uc"
        ),
    )
    __repr_fields__ = ("team", "label", "date", "period")

    team_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("teams.id"), nullable=False
    )
    team = db.relationship("Team", back_populates="worst")
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    period = db.Column(db.Enum(Periods), nullable=False, unique=False)
    data = db.Column(MutableDict.as_mutable(JSONType), default={}, nullable=False)

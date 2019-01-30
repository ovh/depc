from depc.extensions import db
from depc.models import BaseModel


class Log(BaseModel):

    __tablename__ = "logs"
    __repr_fields__ = ("level", "message", "key")

    level = db.Column(db.String(10), nullable=False)
    message = db.Column(db.String(), nullable=False)
    key = db.Column(db.String(50), nullable=False)

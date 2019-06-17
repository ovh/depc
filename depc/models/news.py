from sqlalchemy.schema import UniqueConstraint
from sqlalchemy_utils import UUIDType

from depc.extensions import db
from depc.models import BaseModel


users_news_association_table = db.Table(
    "users_news",
    db.Column(
        "user_id", UUIDType(binary=False), db.ForeignKey("users.id"), primary_key=True
    ),
    db.Column(
        "news_id", UUIDType(binary=False), db.ForeignKey("news.id"), primary_key=True
    ),
    UniqueConstraint("user_id", "news_id", name="users_news_uix"),
)


class News(BaseModel):

    __tablename__ = "news"

    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(), nullable=False)
    users = db.relationship(
        "User", backref=db.backref("news", uselist=True), secondary="users_news"
    )

import enum

from flask_login import UserMixin
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_utils import UUIDType

from depc.extensions import db
from depc.models import BaseModel


class RoleNames(enum.Enum):
    member = "member"
    editor = "editor"
    manager = "manager"


class Grant(BaseModel):
    __tablename__ = "grants"

    user_id = db.Column(UUIDType(binary=False), db.ForeignKey("users.id"))
    user = db.relationship("User", backref="grants")

    role = db.Column(db.Enum(RoleNames), nullable=False, unique=False)

    team_id = db.Column(UUIDType(binary=False), db.ForeignKey("teams.id"))
    team = db.relationship("Team", backref="grants")

    def __repr__(self):
        return "<Grant '{0}' is {1} of {2}>".format(
            self.user.name, self.role.value, self.team.name
        )


class User(BaseModel, UserMixin):

    __tablename__ = "users"
    __repr_fields__ = ("name",)

    name = db.Column(db.String(255), nullable=False, unique=True)
    admin = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean(), default=True)

    teams = association_proxy("grants", "team")

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def is_admin(self):
        return self.admin

    def get_id(self):
        return self.id

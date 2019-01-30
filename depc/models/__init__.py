import datetime
import uuid

import jsonschema
from sqlalchemy import inspect
from sqlalchemy_utils import UUIDType

from depc.extensions import db


def get_uuid():
    return str(uuid.uuid4())


class BaseModel(db.Model):

    __abstract__ = True

    # A tuple of field names that will be used in the model repr
    __repr_fields__ = ()

    id = db.Column(
        UUIDType(binary=False), primary_key=True, nullable=False, default=get_uuid
    )
    created_at = db.Column(
        db.DateTime(timezone=True), default=db.func.now(), nullable=False, index=True
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    def to_dict(self):
        """Serialize an object to a dict"""

        # When committed, an ORM object is expired, which means that
        # obj.__dict__ does not return its properties.
        # session.refresh reloads the object from database
        # http://docs.sqlalchemy.org/en/latest/orm/
        # session_state_management.html#refreshing-expiring
        state = inspect(self)
        if state.expired and state._attached:
            db.session.refresh(self)

        d = dict(self.__dict__)

        # Remove SQLAlchemy stuff
        try:
            del d["_sa_instance_state"]
        except KeyError:
            pass

        return d

    def check_integrity(self):
        """Custom integrity checks beyond schema."""
        self._check_base_integrity()

    def _check_base_integrity(self):
        data = self.to_dict()
        if self.id:
            uuid.UUID(str(self.id))
            del data["id"]
        self._is_datetime_or_none("created_at")
        self._is_datetime_or_none("updated_at")

        # Do not check datetimes with schema
        keys_to_remove = list()
        for key, value in data.items():
            if isinstance(value, datetime.datetime):
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del data[key]

        try:
            jsonschema.validate(data, self._schema)
        except jsonschema.ValidationError as e:
            raise ValueError(str(e))
        except AttributeError:
            pass

    def _is_datetime_or_none(self, attribute):
        value = self.__getattribute__(attribute)
        if value:
            if not isinstance(value, datetime.datetime):
                raise ValueError("{} is not a valid date".format(attribute))

    def __repr__(self):
        """Generate a repr using the model __repr_fields__ or a default repr.

        Example: if a model class depc has a __repr_fields__ = ('x', ), the
        generated repr will be <depc x=someval>

        If no __repr_fields__ is defined, only the id will be displayed.

        """
        if self.__repr_fields__:
            return "<{} {}>".format(
                self.__class__.__name__,
                ", ".join(
                    [
                        "{}={}".format(attr, str(getattr(self, attr, None)))
                        for attr in self.__repr_fields__
                    ]
                ),
            )
        return "<{} '{}'>".format(self.__class__.__name__, self.id)

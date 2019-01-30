import logging

from depc.extensions import db
from depc.models.logs import Log


class DatabaseHandler(logging.Handler):
    def emit(self, record):
        extra = record.__dict__

        log = Log(
            level=record.__dict__["levelname"],
            message=record.__dict__["msg"],
            key=extra.get("result_key"),
        )
        db.session.add(log)
        db.session.commit()

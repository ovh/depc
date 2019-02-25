import logging

from loguru import logger

from depc.extensions import db
from depc.models.logs import Log


class DatabaseHandler(logging.Handler):
    def emit(self, record):
        log = Log(
            level=record.levelname, message=record.getMessage(), key=record.result_key
        )

        db.session.add(log)
        db.session.commit()


class InterceptHandler(logging.StreamHandler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())

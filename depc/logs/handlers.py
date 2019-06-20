import logging

from loguru import logger


class InterceptHandler(logging.StreamHandler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelname, record.getMessage())

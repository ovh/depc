import logging
from logging import config

import celery.signals


@celery.signals.setup_logging.connect
def setup_logging(*args, **kwargs):
    """Hack to prevent Celery from messing with loggers.

    See https://github.com/celery/celery/issues/1867
    """
    pass


def setup_loggers(app):
    """Setup loggers for a production environment"""
    logging_conf = app.config.get("LOGGING", {})
    if not logging_conf:
        return

    logging_conf["version"] = 1
    # inject app, dirty but only way
    for filter_conf in logging_conf.get("filters", {}).values():
        filter_conf["app"] = app

    # setup logging
    config.dictConfig(logging_conf)

    # mute werkzeug (sends duplicates)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

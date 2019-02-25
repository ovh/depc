import logging
import re
import sys

import celery.signals
from loguru import logger

from depc.logs.handlers import DatabaseHandler, InterceptHandler


@celery.signals.setup_logging.connect
def setup_logging(*args, **kwargs):
    """Hack to prevent Celery from messing with loggers.

    See https://github.com/celery/celery/issues/1867
    """
    pass


def setup_loggers(app):
    logging_config = app.config["LOGGING"]
    logging_level = logging.getLevelName(logging_config["level"])

    root_logger = logging.getLogger()
    root_logger.addHandler(InterceptHandler())
    root_logger.setLevel(logging_level)

    app.logger.handlers = []
    app.logger.propagate = True

    # Match some Flask messages
    # e.g.: '127.0.0.1 - - [01/Mar/2019 11:11:32] "GET /v1/teams/
    #        1793e9bc-4724-477d-8d8e-a494b242d454/qos?start=1548979200&end=1551398399
    #        HTTP/1.1" 200 -'
    regex = re.compile(r"\b((?:\d{1,3}\.){3}\d{1,3})\b - - \[.*\] \"(.*)\" (\d{1,3}) -")

    def stdout_filter(record):
        # Flask logging are handled by the Werkzeug module
        if record["name"] == "werkzeug._internal":
            flask_msg = regex.match(record["message"])
            if flask_msg:
                # Rewrite message with the wanted values
                record["message"] = "{} {} {}".format(
                    flask_msg.group(1), flask_msg.group(2), flask_msg.group(3)
                )

        return True

    stdout_sink = {"sink": sys.stdout, "filter": stdout_filter, "level": logging_level}
    logging_format = logging_config.get("format")
    if logging_format:
        stdout_sink.update({"format": logging_format})

    logger.configure(
        handlers=[
            {
                "sink": DatabaseHandler,
                "filter": lambda record: "result_key" in record["extra"],
                "format": "{message}",
            },
            stdout_sink,
        ]
    )

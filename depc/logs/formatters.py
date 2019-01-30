import logging
import time


def style(*styles):
    return "\033[{}m".format(";".join(styles))


class ColoredFormatter(logging.Formatter):
    class COLORS(object):
        reset = style("0")
        bold = style("1")
        no_bold = style("21")

        critical = style("48", "5", "1", "38", "5", "11", "1")  # RED BG YELLOW FG BOLD
        error = style("38", "5", "1")  # RED
        warning = style("38", "5", "11")  # YELLOW
        info = style("38", "5", "2")  # GREEN
        debug = style("38", "5", "12")  # BLUE
        other = style("38", "5", "5")  # PURPLE

    @staticmethod
    def colorize(msg, style_str, end="\033[0m"):
        return "{}{}{}".format(style_str, msg, end)

    @classmethod
    def colorize_record(cls, record, attr, style_str, end=None):
        if hasattr(record, attr):
            setattr(
                record,
                attr,
                cls.colorize(
                    getattr(record, attr), style_str, end if end else cls.COLORS.reset
                ),
            )

    def format(self, record_):
        record_dict = {k: getattr(record_, k) for k in dir(record_)}
        extras = {
            k: v
            for k, v in record_dict.items()
            if not k.startswith("_") and not callable(v)
        }

        # copy record to update attributes without update other handlers' record
        if isinstance(extras["args"], dict):
            extras["args"] = (extras["args"],)
        record = logging.LogRecord(level=record_.levelno, **extras)

        # only colorize elements of record,
        # formatting is done by default formatter
        # with user defined format string
        msg_color = self.COLORS.other
        if record.levelno >= logging.CRITICAL:
            msg_color = self.COLORS.critical
        elif record.levelno >= logging.ERROR:
            msg_color = self.COLORS.error
        elif record.levelno >= logging.WARNING:
            msg_color = self.COLORS.warning
        elif record.levelno >= logging.INFO:
            msg_color = self.COLORS.info
        elif record.levelno >= logging.DEBUG:
            msg_color = self.COLORS.debug

        record.msg_color = msg_color

        # The name of the logger used to log the event represented by this LogRecord.
        self.colorize_record(record, "name", self.COLORS.other)
        # The full pathname of the source file where the logging call was made.
        self.colorize_record(record, "pathname", self.COLORS.other)
        # The line number in the source file where the logging call was made.
        self.colorize_record(record, "lineno", self.COLORS.info)
        # The name of the function or method from which the logging call was invoked.
        self.colorize_record(record, "func", self.COLORS.info)

        # The event description message, possibly a format string with placeholders for variable data.
        self.colorize_record(record, "msg", msg_color)

        # call super to fill other attributes, rest of logging will be in formatMessage/Exception/Stack
        return super(ColoredFormatter, self).format(record)

    def formatMessage(self, record):
        msg_color = record.msg_color

        # Human-readable time when the LogRecord was created.
        self.colorize_record(record, "asctime", self.COLORS.debug)
        # Time when the LogRecord was created (as returned by time.time()).
        self.colorize_record(record, "created", self.COLORS.debug)
        # Filename portion of pathname.
        self.colorize_record(record, "filename", self.COLORS.other)
        # Name of function containing the logging call.
        self.colorize_record(record, "funcName", self.COLORS.info)
        # Text logging level for the message ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
        self.colorize_record(record, "levelname", msg_color)
        # Module (name portion of filename).
        self.colorize_record(record, "module", self.COLORS.other)
        # Millisecond portion of the time when the LogRecord was created.
        self.colorize_record(record, "msecs", self.COLORS.debug)
        # Name of the logger used to log the call.
        self.colorize_record(record, "name", self.COLORS.info)
        # Full pathname of the source file where the logging call was issued (if available).
        self.colorize_record(record, "pathname", self.COLORS.other)
        # Process ID (if available).
        self.colorize_record(record, "process", self.COLORS.other)
        # Process name (if available).
        self.colorize_record(record, "processName", self.COLORS.other)
        # Time in milliseconds when the LogRecord was created, relative to the time the logging module was loaded.
        self.colorize_record(record, "relativeCreated", self.COLORS.debug)
        # Thread ID (if available).
        self.colorize_record(record, "thread", self.COLORS.other)
        # Thread name (if available).
        self.colorize_record(record, "threadName", self.COLORS.other)

        return super(ColoredFormatter, self).formatMessage(record)

    def formatException(self, ei):
        s = super(ColoredFormatter, self).formatException(ei)
        return self.colorize(s, self.COLORS.error)

    def formatStack(self, stack_info):
        return self.colorize(stack_info, self.COLORS.warning)

    def formatTime(self, record, datefmt=None):
        if datefmt:
            return super(ColoredFormatter, self).formatTime(record, datefmt)

        ct = self.converter(record.created)
        s = time.strftime("%d/%m-%H:%M:%S", ct)
        return s

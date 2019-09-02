import json


class GraylogExtendedLogFormatSink:
    """
    Log outputs into the Graylog Extended Log Format, a.k.a. GELF.
    """

    def __init__(self, host="depc"):
        self.host = host

    def _transform_record_to_gelf(self, serialized_record):
        json_record = json.loads(serialized_record)["record"]

        # According to the documentation, extra fields are prefixed with "_".
        # See: https://docs.graylog.org/en/latest/pages/gelf.html#gelf-payload-specification
        payload = {
            "version": "1.1",
            "host": self.host,
            "short_message": json_record["message"],
            "level": json_record["level"]["name"],
            "timestamp": json_record["time"]["timestamp"],
            # "file" and "line" are sent as additional fields
            "_file": json_record["file"]["path"],
            "_line": json_record["line"],
        }

        # Add extra fields from logger.bind() to payload.
        for k, v in json_record["extra"].items():
            payload["_" + k] = v

        return json.dumps(payload)

    def write(self, record):
        print(self._transform_record_to_gelf(record))

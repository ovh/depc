import datetime

from depc.controllers import Controller
from depc.controllers import NotFoundError, RequirementsNotSatisfiedError
from depc.extensions import redis
from depc.models.worst import Periods
from depc.models.worst import Worst


def validate_date(date_text):
    try:
        datetime.datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        raise RequirementsNotSatisfiedError(
            "Invalid date format (expected: YYYY-MM-DD)"
        )


class WorstController(Controller):

    model_cls = Worst

    @classmethod
    @redis.cache(period=redis.seconds_until_midnight)
    def get_daily_worst_items(cls, team_id, label, date):
        validate_date(date)
        try:
            worst_items = WorstController.get(
                filters={
                    "Worst": {
                        "team_id": team_id,
                        "label": label,
                        "period": Periods.daily,
                        "date": date,
                    }
                }
            )

            return [
                {"name": name, "qos": qos} for name, qos in worst_items["data"].items()
            ]
        except NotFoundError:
            return []

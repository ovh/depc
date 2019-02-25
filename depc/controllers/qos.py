from depc.controllers import Controller
from depc.extensions import redis
from depc.queries import (
    QOS_ITEM_PER_TEAM_LABEL,
    QOS_WORST_ITEM_PER_LABEL,
    QOS_PER_TEAM,
    QOS_FILTERED_BY_LABEL,
)
from depc.utils.warp10 import Warp10Client, _transform_warp10_values


class QosController(Controller):
    @classmethod
    @redis.cache(period=redis.seconds_until_midnight)
    def get_team_qos(cls, team_id, label, start, end):
        cls.check_valid_period(start, end)
        client = Warp10Client()

        # Default values
        params = {"team": team_id}

        script = QOS_PER_TEAM
        if label:
            script = QOS_FILTERED_BY_LABEL
            params.update({"name": label})

        client.generate_script(start=start, end=end, script=script, extra_params=params)
        resp = client.execute()

        # Return list of datapoints
        if label:
            try:
                return _transform_warp10_values(resp[0][0]["v"])
            except IndexError:
                return {}

        # Order by Label
        data = {}

        for metrics in resp[0]:
            label = metrics["l"]["name"]

            if label not in data:
                data[label] = {}
            data[label] = _transform_warp10_values(metrics["v"])

        return data

    @classmethod
    @redis.cache(period=redis.seconds_until_midnight)
    def get_team_item_qos(cls, team, label, name, start, end):
        cls.check_valid_period(start, end)
        client = Warp10Client()

        client.generate_script(
            start=start,
            end=end,
            script=QOS_ITEM_PER_TEAM_LABEL,
            extra_params={"team": team, "label": label, "name": name},
        )
        resp = client.execute()

        # No result
        if not resp[0]:
            return {}

        values = _transform_warp10_values(resp[0][0]["v"])
        return values

    @classmethod
    @redis.cache(period=redis.seconds_until_midnight)
    def get_label_worst_items(cls, team, label, start, end, count):
        cls.check_valid_period(start, end)
        client = Warp10Client()

        client.generate_script(
            start=start,
            end=end,
            script=QOS_WORST_ITEM_PER_LABEL,
            extra_params={"team": team, "label": label, "count": str(count)},
        )

        resp = client.execute()

        # No result
        if not resp[0]:
            return {}

        data = []
        for metric in resp[0]:
            data.append({"name": metric["l"]["name"], "qos": metric["v"][0][1]})

        return data

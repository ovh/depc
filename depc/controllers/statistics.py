from depc.controllers import Controller
from depc.extensions import redis
from depc.queries import STATISTICS_SCRIPT
from depc.utils.warp10 import Warp10Client


class StatisticsController(Controller):
    @classmethod
    @redis.cache(period=redis.seconds_until_midnight)
    def get_team_statistics(
        cls, team_id, start, end, label=None, type=None, sort="label"
    ):
        cls.check_valid_period(start, end)
        client = Warp10Client()

        filter_str = " "
        if label:
            filter_str += "'label' '{0}' ".format(label)
        if type:
            filter_str += "'type' '{0}' ".format(type)

        client.generate_script(
            start=start,
            end=end,
            script=STATISTICS_SCRIPT,
            extra_params={"team": team_id, "filter": filter_str},
        )
        resp = client.execute()

        # No result
        if not resp[0]:
            return {}

        # Sort the results
        sort_choices = ["label", "type"]
        main_sort = sort_choices.pop(
            sort_choices.index(sort if sort in sort_choices else "label")
        )
        second_sort = sort_choices.pop()

        result = {}

        # We want to have some statistics for all labels
        # (ex: total number of nodes for the team)
        if sort == "label":
            result["*"] = {}

        for statistic in resp[0]:
            main = statistic["l"][main_sort]
            second = statistic["l"][second_sort]

            if main not in result:
                result[main] = {}

            if second not in result[main]:
                result[main][second] = {}

            # Total of stats for all labels
            if sort == "label":
                if second not in result["*"]:
                    result["*"][second] = {}

            for v in statistic["v"]:
                ts = int(v[0] / 1000000)  # ms to s
                result[main][second][ts] = v[1]

                # Increment the total
                if sort == "label":
                    if ts not in result["*"][second]:
                        result["*"][second][ts] = 0
                    result["*"][second][ts] += v[1]

        return result

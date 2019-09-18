import hashlib
import inspect
import json
import pickle
import re
import time
from functools import wraps

import arrow
import redis
from loguru import logger


class CacheJSONEncoder(json.JSONEncoder):
    """JSON encoder that transforms Arrow
    objects to their string representation."""

    def default(self, o):
        try:
            return json.JSONEncoder.default(self, o)
        except TypeError:
            return str(o)


class RedisCache(redis.Redis):
    DURATION_REGEX = re.compile(
        r"P((?P<years>\d+)Y)?((?P<months>\d+)M)?((?P<weeks>\d+)W)?((?P<days>\d+)D)?"
        r"T((?P<hours>\d+)H)?((?P<minutes>\d+)M)?((?P<seconds>\d+)S)?",
        re.IGNORECASE,
    )

    def __init__(self, *args, **kwargs):
        try:
            connection_pool = redis.ConnectionPool.from_url(*args, **kwargs)
        except Exception:
            connection_pool = redis.ConnectionPool(*args, **kwargs)

        super(RedisCache, self).__init__(connection_pool=connection_pool)

    def cache(self, period="1h", quantity=None, prefix="cache_"):
        """
        Decorator to cache function results for a period of time.
        Results will be cache depending on function arguments.
        Wrapped function will have a `clear()` method to clear all
        or partial part of the cache

        Args:
            period: a period range in second, or a string, None for no expiration
            quantity: number of different element to cache, older will be replaced.
            prefix: a prefix for the key

        Returns:
            func: wrapper of function
        """

        def decorator(func):
            func_name = "{}.{}".format(func.__module__, func.__name__)

            @wraps(func)
            def wrapper(*args, **kwargs):
                key_name = self.get_key_name(
                    func, func_name, None, None, *args, **kwargs
                )

                if prefix:
                    key_name = "{}_{}".format(prefix, key_name)

                # check cache validity
                ttl = self.ttl(key_name)
                if ttl and ttl > 0:
                    try:
                        result_serialized = self.get(key_name)
                        result = pickle.loads(result_serialized)
                        logger.debug(
                            "Fetched: {}(*{}, **{}) at {}".format(
                                func_name, args, kwargs, key_name
                            )
                        )

                        # if cache is size limited, control the size
                        if quantity and quantity > 0:
                            self.control_quantity(func_name, quantity)

                        return result
                    except Exception as exc:
                        logger.error("Fetch serialization failed: {}".format(exc))

                # exec & create cache
                res = func(*args, **kwargs)
                try:
                    result_serialized = pickle.dumps(
                        res, protocol=pickle.HIGHEST_PROTOCOL
                    )

                    self.set(
                        key_name, result_serialized, ex=self.get_period_seconds(period)
                    )

                    # if cache is size limited, store our pointer and control size
                    if quantity:
                        self.rpush(func_name, key_name)
                        self.control_quantity(func_name, quantity)

                    logger.debug(
                        "Caching: {}(*{}, **{}) at {}".format(
                            func_name, args, kwargs, key_name
                        )
                    )
                except Exception as exc:
                    logger.error("Caching serialization failed: {}".format(exc))
                finally:
                    return res

            # append methods to wrapper
            def cache_clear_all():

                key_name = "{}*".format(func_name)
                if prefix:
                    key_name = "{}_{}".format(prefix, key_name)
                logger.debug("Erasing all caches for {}".format(key_name))
                keys = self.keys(key_name)
                if keys:
                    self.delete(*keys)

            setattr(wrapper, "cache_clear_all", cache_clear_all)

            def cache_bypass(*args, **kwargs):
                logger.debug("Bypassing cache for {}".format(func_name))
                return func(*args, **kwargs)

            setattr(wrapper, "cache_bypass", cache_bypass)

            def cache_clear(*args, **kwargs):
                key_name = self.get_key_name(
                    func, func_name, None, None, *args, **kwargs
                )
                logger.debug("Erasing cache for {}".format(key_name))
                self.delete(key_name)

            setattr(wrapper, "cache_clear", cache_clear)

            def cache_refresh(*args, **kwargs):
                key_name = self.get_key_name(
                    func, func_name, None, None, *args, **kwargs
                )
                logger.debug("Refreshing cache for {}".format(key_name))
                res = func(*args, **kwargs)
                result_serialized = pickle.dumps(res, protocol=pickle.HIGHEST_PROTOCOL)
                self.set(
                    key_name, result_serialized, ex=self.get_period_seconds(period)
                )
                return res

            setattr(wrapper, "cache_refresh", cache_refresh)

            return wrapper

        return decorator

    @classmethod
    def get_key_name(
        cls, func, func_name, team_name_override, label_name_override, *args, **kwargs
    ):
        """
        team_name_override and label_name_override parameters should only be used if no func parameter can be provided.
        That means you should not override team and label when passing a func in general except if you really
        know what you are doing.
        You should also not pass a func if you override team and label using team_name_override and
        label_name_override in general except if you really know what you are doing.
        These parameters do not have default values and they use this comment as a warning instead because adding
        default values would cause problems with *args and **kwargs if not all of the parameters are provided.

        The point of these three parameters is to have the team and the label name in the Redis keys names if available.
        If not, we will use the names "noteam" and "nolabel" instead.
        """
        from depc.controllers.teams import TeamController

        # retrieve key from func attributes
        func_signature = {"args": args, "kwargs": kwargs}

        # Init team and label names data
        team_data_set = False
        label_set = False
        team_data = ""
        label = ""

        # Get the team and label from the override first if provided
        if team_name_override:
            team_data = team_name_override
            team_data_set = True
        if label_name_override:
            label = label_name_override
            label_set = True

        # Get the team and label from kwargs if possible (and if not already set before)
        if "team" in kwargs and not team_data_set:
            team_data = kwargs["team"]
            team_data_set = True
        elif "team_id" in kwargs and not team_data_set:
            team_data = kwargs["team_id"]
            team_data_set = True

        if "label" in kwargs and not label_set:
            label = kwargs["label"]
            label_set = True

        # Get the team and label from func args if possible (and if not already set before)
        if func and (not team_data_set or not label_set):
            team_data_index_found = False
            label_index_found = False
            team_data_index = 0
            label_index = 0
            for index, param_name in enumerate(
                inspect.signature(func).parameters.keys()
            ):
                if param_name == "team" or param_name == "team_id":
                    team_data_index = index
                    team_data_index_found = True
                if param_name == "label":
                    label_index = index
                    label_index_found = True
            # Set the team and label names if the func arg names match (and if they have not already been set before)
            if not team_data_set and team_data_index_found:
                team_data = args[team_data_index]
                team_data_set = True
            if not label_set and label_index_found:
                label = args[label_index]
                label_set = True

        if not team_data_set or not team_data:
            # Give a default value to the team name if team data is not found / not available
            team_name = "__noteam__"
        else:
            # Format the team name if team data is found:
            if re.match(
                "[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}",
                team_data,
            ):
                # If the team data is a team UUID, get the team name
                team_name = TeamController.get({"Team": {"id": team_data}})["name"]
            else:
                # Else, we already have a team name and we use it directly
                team_name = team_data
            team_name = "".join(e for e in team_name if e.isalnum()).lower()

        if not label_set or not label:
            # Give a default value to the label name if label data is not found / not available
            label = "__nolabel_"

        try:
            func_signature_serialized = json.dumps(
                func_signature, sort_keys=True, cls=CacheJSONEncoder
            )
            func_signature_hash = hashlib.new(
                "md5", func_signature_serialized.encode("utf-8")
            ).hexdigest()[:16]
        except Exception:
            func_signature_hash = "{:x}".format(int(time.perf_counter() * 100000000000))

        key_name = "{}.{}.{}_{}".format(
            func_name, team_name, label, func_signature_hash
        )
        return key_name

    @classmethod
    def get_period_seconds(cls, period):
        if not period:
            return None

        if isinstance(period, int):
            period_seconds = period
        elif isinstance(period, str):
            match = cls.DURATION_REGEX.match(period)
            assert match, "Invalid period"

            until = arrow.Arrow(**match.groupdict())
            period_seconds = (until - arrow.utcnow()).seconds
        elif callable(period):
            period_seconds = int(period())
        else:
            raise Exception("Period must be a string, int or callable")

        assert period_seconds > 0, "Period must be more than 1s"
        return period_seconds

    def control_quantity(self, key, quantity):
        overflow = self.llen(key) - quantity
        while overflow > 0:
            old_key = self.lpop(key)
            self.delete(old_key)
            overflow -= 1

    @staticmethod
    def seconds_until_midnight():
        return (arrow.utcnow().ceil("day") - arrow.utcnow()).seconds

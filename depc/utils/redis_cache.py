import hashlib
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
                key_name = self.get_key_name(func_name, *args, **kwargs)

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
                key_name = self.get_key_name(func_name, *args, **kwargs)
                logger.debug("Erasing cache for {}".format(key_name))
                self.delete(key_name)

            setattr(wrapper, "cache_clear", cache_clear)

            def cache_refresh(*args, **kwargs):
                key_name = self.get_key_name(func_name, *args, **kwargs)
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
    def get_key_name(cls, func_name, *args, **kwargs):
        # retrieve key from func attributes
        func_signature = {"args": args, "kwargs": kwargs}

        try:
            func_signature_serialized = json.dumps(
                func_signature, sort_keys=True, cls=CacheJSONEncoder
            )
            func_signature_hash = hashlib.new(
                "md5", func_signature_serialized.encode("utf-8")
            ).hexdigest()[:16]
        except Exception:
            func_signature_hash = "{:x}".format(int(time.perf_counter() * 100000000000))

        key_name = "{}_{}".format(func_name, func_signature_hash)
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

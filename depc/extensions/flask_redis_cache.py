from depc.utils.redis_cache import RedisCache


class FlaskRedisCache(RedisCache):
    def __init__(self, app=None, config_prefix="REDIS_CACHE"):
        if app is not None:
            self.init_app(app, config_prefix)

    def init_app(self, app, config_prefix="REDIS_CACHE"):
        app_config = app.config.get(config_prefix, {})
        RedisCache.__init__(self, **app_config)

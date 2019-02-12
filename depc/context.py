import os

from depc import BASE_DIR
from depc.extensions import (
    admin,
    cel,
    cors,
    db,
    jsonschema,
    migrate,
    flask_encrypted_dict,
    login_manager,
    redis,
    redis_scheduler,
)
from depc.logs import setup_loggers


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "mysecret"
    JSON_AS_ASCII = False
    DEBUG = False
    LOGGERS = {}
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    CELERY_RETRY_DELAY = 60
    CELERY_CONF = {
        "CELERY_TASK_SERIALIZER": "json",
        "CELERY_RESULT_SERIALIZER": "json",
        "CELERY_ACCEPT_CONTENT": ["json"],
        "CELERYD_HIJACK_ROOT_LOGGER": False,
        "CELERYD_POOL": "solo",
    }
    JSONSCHEMA_DIR = os.path.join(BASE_DIR, "schemas")
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    @staticmethod
    def init_app(app):
        cel.init_app(app)
        with app.app_context():
            db.init_app(app)
        migrate.init_app(app, db)
        flask_encrypted_dict.init_app(app)
        jsonschema.init_app(app)
        redis.init_app(app)
        redis_scheduler.init_app(app, config_prefix="REDIS_SCHEDULER_CACHE")
        login_manager.init_app(app)
        cors.init_app(app)
        setup_loggers(app)


class TestingConfig(Config):
    DEBUG = True

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        admin.init_app(app)


class DevelopmentConfig(Config):
    DEBUG = True

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        admin.init_app(app)


class ProductionConfig(Config):
    DEBUG = False

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        admin.init_app(app)


class SnakeoilConfig(Config):
    TESTING = True
    DEBUG = True

    @staticmethod
    def init_app(app):
        Config.init_app(app)


# Aliases
DevConfig = DevelopmentConfig
ProdConfig = ProductionConfig
TestConfig = TestingConfig

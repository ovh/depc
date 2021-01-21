import logging
import os
from pathlib import Path

from depc import BASE_DIR
from depc.extensions import (
    admin,
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
    BASE_UI_URL = "http://127.0.0.1/"
    SECRET_KEY = os.environ.get("SECRET_KEY") or "mysecret"
    JSON_AS_ASCII = False
    DEBUG = False
    LOGGERS = {}
    LOGGING = {"level": "DEBUG"}
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    NEO4J = {
        "url": "http://127.0.0.1:7474",
        "uri": "bolt://127.0.0.1:7687",
        "username": "neo4j",
        "password": "neo4j",
        "encrypted": False,
    }
    CONSUMER = {
        "kafka": {
            "hosts": "localhost:9093",
            "batch_size": 10,
            "topics": ["depc.my_topic"],
            "username": "depc.consumer",
            "password": "p4ssw0rd",
            "client_id": "depc.consumer",
            "group_id": "depc.consumer.depc_consumer_group",
        }
    }
    JSONSCHEMA_DIR = str(Path(BASE_DIR) / "schemas")
    STATIC_DIR = str(Path(BASE_DIR) / "static")
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    MAX_WORST_ITEMS = 15
    EXCLUDE_FROM_AUTO_FILL = []

    @staticmethod
    def init_app(app):
        setup_loggers(app)
        with app.app_context():
            db.init_app(app)
        migrate.init_app(app, db)
        flask_encrypted_dict.init_app(app)
        jsonschema.init_app(app)
        redis.init_app(app)
        redis_scheduler.init_app(app, config_prefix="REDIS_SCHEDULER_CACHE")
        login_manager.init_app(app)
        cors.init_app(app)


class TestingConfig(Config):
    DEBUG = True
    NEO4J = {
        **Config.NEO4J,
        "password": "foobar",
    }

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

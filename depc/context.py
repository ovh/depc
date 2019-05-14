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
        "password": "p4ssw0rd",
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
    KAFKA_CONFIG = {
        "hosts": "localhost:9093",
        "topic": "depc.config",
        "username": "depc.writer",
        "password": "p4ssw0rd",
        "client_id": "depc.writer"
    }
    JSONSCHEMA_DIR = str(Path(BASE_DIR) / "schemas")
    SQLALCHEMY_TRACK_MODIFICATIONS = True

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

import codecs
import datetime
import importlib
import json
import os
import pkgutil
from pathlib import Path

import pandas
import yaml
from flask import Flask
from flask.json import JSONEncoder
from flask.wrappers import Request
from werkzeug.routing import Rule

BASE_DIR = str(Path(__file__).resolve().parent)


class ExtendedRequest(Request):
    @property
    def json(self):
        return self.get_json(force=True)


# from http://flask.pocoo.org/snippets/35/
class ReverseProxied(object):
    """
    Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    :param app: the WSGI application
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get("HTTP_X_SCRIPT_NAME", "")
        if script_name:
            environ["SCRIPT_NAME"] = script_name
            path_info = environ["PATH_INFO"]
            if path_info.startswith(script_name):
                environ["PATH_INFO"] = path_info[len(script_name) :]

        scheme = environ.get("HTTP_X_FORWARDED_PROTO", "")
        server = environ.get("HTTP_X_FORWARDED_SERVER", "")
        if server:
            environ["HTTP_HOST"] = server
        if "https" in scheme:
            environ["wsgi.url_scheme"] = "https"
            environ["HTTP_X_FORWARDED_SERVER"] = "https"
        return self.app(environ, start_response)


class ExtendedRule(Rule):
    def __init__(self, *args, **kwargs):
        self.request_schema = kwargs.pop("request_schema", None)
        self.response_schema = kwargs.pop("response_schema", None)
        super().__init__(*args, **kwargs)


class ExtendedJSONEncoder(JSONEncoder):
    """JSON encoder that transforms datetimes to RFC 3339"""

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(o, pandas.core.series.Series):
            return o.to_dict()
        else:
            return JSONEncoder.default(self, o)


class ExtendedFlask(Flask):
    request_class = ExtendedRequest
    url_rule_class = ExtendedRule
    json_encoder = ExtendedJSONEncoder


def read_config(config_file, verbose=False):
    # Locate the config file to use
    if not os.path.isfile(config_file):
        print("Missing configuration file")
        return {}
    if verbose:
        print("Using configuration file: %s" % config_file)

    # Open and read the config file
    with codecs.open(config_file, "r", "utf8") as file_handler:
        conf = yaml.load(file_handler)
    if conf is None:
        conf = {}
    if verbose:
        print(json.dumps(conf, sort_keys=True, indent=4, separators=(",", ": ")))
    return conf


def import_submodules(package, modules_to_import):
    """ Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :param modules_to_import: modules_to_import
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}

    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        if not name.startswith("_") and not name.startswith("tests"):
            full_name = package.__name__ + "." + name

            if any((x in package.__name__ for x in modules_to_import)) or any(
                (x in name for x in modules_to_import)
            ):
                results[full_name] = importlib.import_module(full_name)
                if is_pkg:
                    results.update(import_submodules(full_name, modules_to_import))
    return results


def create_app(environment="dev"):
    context = importlib.import_module("depc.context")
    conf_cls = getattr(context, "{}Config".format(environment.capitalize()))
    conf_file = str(
        Path(os.getenv("DEPC_HOME", str(Path(__file__).resolve().parents[1])))
        / "depc.{}.yml".format(environment)
    )

    # Import all modules
    import_submodules(__name__, ("models", "sources", "tasks", "apiv1"))

    # Import the admin module
    from depc import admin

    app = ExtendedFlask(__name__)
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    # Load the environment
    app.config.from_object(conf_cls)
    data_file = read_config(conf_file)
    app.config.update(data_file)
    app.config["CELERY_CONF"].update(conf_cls.CELERY_CONF)

    # Load extensions
    conf_cls.init_app(app)

    from depc.apiv1 import api as apiv1_blueprint

    app.register_blueprint(apiv1_blueprint, url_prefix="/v1")

    return app

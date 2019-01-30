import datetime
import json
import re
from copy import deepcopy
from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from flask_jsonschema import _validate

# We need to import these controllers
# to use it in Flask-Admin
from depc.controllers.teams import TeamController
from depc.controllers.grants import GrantController


class ExtendedBlueprint(Blueprint):
    def route(self, rule, **options):
        """Like :meth:`Flask.route` but for a blueprint.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the blueprint.
        """
        for method in options.get("methods", []):
            allowed_methods = ("GET", "PUT", "POST", "DELETE")
            if method not in allowed_methods:
                raise ValueError("API only accepts {} methods".format(allowed_methods))

        def decorator_func(f):
            @wraps(f)
            def wrapper_func(*args, **kwargs):
                path = options.get("request_schema")
                if not path:
                    return f(*args, **kwargs)
                jschema = current_app.extensions.get("jsonschema", None)
                if jschema is None:
                    raise RuntimeError(
                        "Flask-JsonSchema was not properly initialized for the"
                        " current application: %s" % current_app
                    )
                schema = deepcopy(jschema.get_schema(path))
                _validate(request.json, schema)
                return f(*args, **kwargs)

            endpoint = options.pop("endpoint", f.__name__)
            self.add_url_rule(rule, endpoint, wrapper_func, **options)

            return wrapper_func

        return decorator_func


api = ExtendedBlueprint("apiv1", __name__)
COMMON_VISIBLE = ["createdAt", "updatedAt", "id"]


class CustomJSONEncoder(json.JSONEncoder):
    """JSON encoder that transforms datetimes to RFC 3339"""

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            return json.JSONEncoder.default(self, o)


def get_payload():
    """Get the body of a JSON formatted request as a snake_case dict."""
    return dict_to_snake_case(request.get_json(force=True))


def single_object(object_data, visible, status_code=200):
    rv = _format_object_fields(object_data, visible)
    return (
        json.dumps(rv, cls=CustomJSONEncoder),
        status_code,
        {"Content-Type": "application/json"},
    )


def _format_object_fields(obj, visible):
    return dict([(k, v) for k, v in dict_to_camel_case(obj).items() if k in visible])


def format_object(obj, visible):
    visible = set(COMMON_VISIBLE + list(visible))
    return _format_object_fields(obj, visible)


def to_snake_case(string):
    """Give the snake_case representation of a camelCase string."""
    return re.sub("(?!^)([A-Z]+)", r"_\1", string).lower()


def to_camel_case(string):
    """Give the camelCase representation of a snake_case string."""
    return re.sub(r"_(\w)", lambda x: x.group(1).upper(), string)


def _dict_to_other_case(d, switch_case_func):
    """Apply switch_case_func to first layer key of a dict."""
    r = dict()
    for key, value in d.items():
        key = switch_case_func(key)
        r[key] = value
    return r


def dict_to_snake_case(d):
    """Convert keys in the first layer of a dict to snake_case."""
    return _dict_to_other_case(d, to_snake_case)


def dict_to_camel_case(d):
    """Convert keys in the first layer of a dict to camelCase."""
    return _dict_to_other_case(d, to_camel_case)


def dict_to_str_dict(d):
    """Convert all values of a dict to string"""
    return {k: str(v) for k, v in d.items()}


@api.route("/ping")
def ping():
    return jsonify({"message": "pong"})

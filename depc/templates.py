import copy
import re
from datetime import datetime

from jinja2.sandbox import ImmutableSandboxedEnvironment


def iso8601_filter(ts):
    """
    Take a timestamp and return it as a ISO8601 formatted date.
    """
    try:
        date = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    except TypeError:
        return ts
    return date


def regex_search_filter(value, pattern, ignorecase=False, multiline=False):
    flag = 0
    if ignorecase:
        flag |= re.I
    if multiline:
        flag |= re.M

    obj = re.search(pattern, value, flag)
    if not obj:
        return None
    return obj.groups()


def regex_search_bool_filter(value, pattern, ignorecase=False, multiline=False):
    groups = regex_search_filter(value, pattern, ignorecase, multiline)
    if groups is None:
        return False
    return True


def to_bool_filter(a):
    return bool(a)


class Template(object):
    def __init__(self, check, context):
        self.check = check
        self.env = ImmutableSandboxedEnvironment()

        _ctx = copy.deepcopy(context)
        self.variables = _ctx.pop("variables", {})
        self.ctx = {"depc": _ctx}

    def _recursive_render(self, tpl):
        """
        A variable can contain itself another variable : we loop until
        the template is finally completely formed.
        """
        new_tpl = self.env.from_string(tpl).render(**self.ctx)
        if new_tpl != tpl:
            return self._recursive_render(new_tpl)
        else:
            return tpl

    def _render_part(self, value):
        """
        Recursively parse a dict and render every part.
        """
        if isinstance(value, str):
            return self._recursive_render(value)
        elif isinstance(value, list):
            for i, l in enumerate(value):
                value[i] = self._render_part(l)
        elif isinstance(value, dict):
            for k, v in value.items():
                value[k] = self._render_part(v)
        return value

    def render(self, context=None):
        if context:
            self.ctx["depc"] = context

        # Add custom filters
        self.env.filters["iso8601"] = iso8601_filter
        self.env.filters["regex_search"] = regex_search_filter
        self.env.filters["regex_search_bool"] = regex_search_bool_filter
        self.env.filters["bool"] = to_bool_filter

        # Add the variables
        self.ctx["depc"]["rule"] = self.variables.get("rule", {})
        self.ctx["depc"]["team"] = self.variables.get("team", {})
        self.ctx["depc"]["check"] = self.variables.get("checks", {}).get(
            self.check.name, {}
        )
        self.ctx["depc"]["source"] = self.variables.get("sources", {}).get(
            self.check.source.name, {}
        )

        parameters = copy.deepcopy(self.check.parameters)
        return self._render_part(parameters)

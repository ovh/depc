import arrow
import requests
from flask import current_app as app
from requests.exceptions import Timeout

import aiohttp

HEADERS = """
$START$ 'start' STORE
$END$ 'end' STORE
"""


class Warp10Exception(Exception):
    pass


def _transform_warp10_values(values):
    values_copy = {}
    for v in values:
        ts = int(v[0] / 1000000)  # ms to s
        values_copy[ts] = v[-1]

    return values_copy


class Warp10Client:
    def __init__(self, url=None, rotoken=None, wtoken=None, script="", use_cache=False):
        self.script = script

        key = "WARP10"
        if use_cache:
            key = "WARP10_CACHE"

        self.rotoken = rotoken if rotoken else app.config[key]["rotoken"]
        self.wtoken = wtoken if wtoken else app.config[key].get("wtoken")
        self.url = url if url else app.config[key]["url"]

    @staticmethod
    def convert_to_iso(ts):
        """
        Convert the timestamp into a valid ISO8601 date.
        :param ts: the timestamp in seconds
        :return: ISO8601 date as a string
        """
        date = "{0}.000000Z".format(arrow.get(ts).isoformat()[:-6])
        return date

    async def async_execute(self):
        url = self.url + "/exec"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=self.script) as r:
                if r.status != 200:
                    raise Warp10Exception(str(r.text))
                resp = await r.json(content_type=None)
        return resp

    def execute(self):
        try:
            resp = requests.post(self.url + "/exec", data=self.script, timeout=60)
        except Timeout as e:
            raise Warp10Exception(str(e))
        else:
            if resp.status_code != 200:
                raise Warp10Exception(resp.content)

        return resp.json()

    def generate_script(self, script, start, end, extra_params=None, max_gts=None):
        # We must convert timestamp values in ISO8601 format
        # [WEBHOSTING-3956] start needs to be a second earlier because of a
        # Warp10 upgrade which does not include the first second
        start = Warp10Client.convert_to_iso(int(start) - 1)
        end = Warp10Client.convert_to_iso(end)

        self.script = ""
        self.script += "'{0}' 'start' STORE\n".format(start)
        self.script += "'{0}' 'end' STORE\n".format(end)

        # Add the read and write tokens
        self.script += "'{0}' 'token' STORE\n".format(self.rotoken)
        if self.wtoken:
            self.script += "'{0}' 'wtoken' STORE\n".format(self.wtoken)

        # if we want higher limits
        if max_gts is not None:
            self.script += "$token AUTHENTICATE\n{0} MAXGTS\n".format(max_gts)

        # Add the whole script
        self.script += script

        # Change all placeholders
        if extra_params:
            params = {k: v for k, v in extra_params.items() if v}
            for k, v in params.items():
                self.script = self.script.replace("${0}$".format(k.upper()), v)

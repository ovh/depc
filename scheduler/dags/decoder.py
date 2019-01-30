import json


class BoolsDpsDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if "bools_dps" not in obj:
            return obj
        obj["bools_dps"] = {int(k): v for k, v in obj["bools_dps"].items()}
        return obj

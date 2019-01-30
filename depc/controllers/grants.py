from depc.controllers import Controller
from depc.models.users import Grant


class GrantController(Controller):

    model_cls = Grant

    @classmethod
    def resource_to_dict(cls, obj, blacklist=False):
        return {"user": obj.user.name, "role": obj.role.value}

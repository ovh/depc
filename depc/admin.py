from flask import abort
from flask import current_app
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import JSONField
from flask_login import current_user

from depc.extensions import admin, db
from depc.models.checks import Check
from depc.models.rules import Rule
from depc.models.sources import Source
from depc.models.teams import Team
from depc.models.users import User, Grant


class AuthModelView(ModelView):
    def is_accessible(self):
        if current_app.config.get("FORCE_INSECURE_ADMIN"):
            return True

        return current_user.is_authenticated and current_user.is_admin()

    def inaccessible_callback(self, name, **kwargs):
        abort(401)


class ExtendedModelView(AuthModelView):
    """Base ModelView of all models."""

    can_edit = True
    can_create = True
    can_export = True
    column_display_pk = False
    column_default_sort = ("id", True)
    page_size = 50
    can_view_details = True

    column_exclude_list = ("id", "created_at", "updated_at")
    column_details_exclude_list = ()
    form_excluded_columns = ("id", "created_at", "updated_at")

    @property
    def column_list(self):
        columns = [col.name for col in self.model.__table__.columns]
        return columns

    def _get_controller(self):
        from depc.controllers import Controller

        for controller in Controller.__subclasses__():
            if controller.model_cls == self.model:
                return controller
        raise Exception("Controller Not Found")

    def get_column_names(self, only_columns, excluded_columns):
        excluded_columns = (
            getattr(self._get_controller(), "hidden_attributes", ())
            + self.column_exclude_list
        )
        excluded_columns = tuple(set(excluded_columns))
        return super().get_column_names(only_columns, excluded_columns)

    def _get_data_from_form(self, form):
        data = {}
        for name, field in form._fields.items():
            field_data = field.data
            if field_data == "":
                field_data = None
            data[name] = field_data
        return data

    def create_model(self, form):
        controller = self._get_controller()
        data = self._get_data_from_form(form)
        return controller._create(data=data)

    def update_model(self, form, model):
        controller = self._get_controller()
        data = self._get_data_from_form(form)

        filters = {type(model).__name__: {"id": model.id}}

        controller._update(data=data, filters=filters)
        return True

    def delete_model(self, model):
        controller = self._get_controller()
        controller._delete({type(model).__name__: {"id": model.id}})
        return True


class RuleModelView(ExtendedModelView):
    column_list = ("name", "description", "team.name")
    column_labels = {"team.name": "Team"}

    def _get_data_from_form(self, form):
        data = super()._get_data_from_form(form)

        # Transform Check objects into list of ID
        checks = data.get("checks", None)
        if checks:
            c = [check.id for check in checks]
            data["checks"] = c

        return data


class SourceModelView(ExtendedModelView):
    column_exclude_list = ("id", "created_at", "updated_at", "configuration")
    column_list = ("name", "plugin", "team.name")
    column_labels = {"team.name": "Team"}
    form_excluded_columns = ("id", "created_at", "updated_at", "source_checks")
    form_overrides = {"configuration": JSONField}


class CheckModelView(ExtendedModelView):
    form_excluded_columns = ("id", "created_at", "updated_at", "rules")
    form_overrides = {"parameters": JSONField}

    def _get_data_from_form(self, form):
        data = super()._get_data_from_form(form)

        # Add the source_id and check_type keys
        data["source_id"] = data["source"].id

        return data


class GrantModelView(ExtendedModelView):
    column_list = ("user.name", "role", "team.name")
    column_labels = {"user.name": "User", "role": "Role", "team.name": "Team"}


admin.add_view(CheckModelView(Check, db.session))
admin.add_view(SourceModelView(Source, db.session))
admin.add_view(RuleModelView(Rule, db.session))
admin.add_view(ExtendedModelView(User, db.session))
admin.add_view(ExtendedModelView(Team, db.session))
admin.add_view(GrantModelView(Grant, db.session))

from flask import jsonify, make_response
from jsonschema.exceptions import ValidationError

from depc.apiv1 import api
from depc.controllers import (
    NotFoundError,
    AlreadyExistError,
    RequirementsNotSatisfiedError,
    IntegrityError,
)
from depc.sources.exceptions import BadConfigurationException


def format_controller_error(e):
    content = {"message": str(e)}
    return jsonify(content)


def format_error(code, message):
    content = {"message": message}
    # We cannot put that in an after_request because they are not triggered
    # when returning a 500
    response = make_response(jsonify(content), code)
    return response


@api.app_errorhandler(NotFoundError)
def not_found_error_handler(e):
    return format_error(404, str(e))


@api.app_errorhandler(ValidationError)
def validation_error_handler(e):
    return format_error(400, e.message)


@api.app_errorhandler(IntegrityError)
def integrity_error_handler(e):
    return format_error(400, str(e))


@api.app_errorhandler(NotImplementedError)
def not_implemented_error_handler(e):
    return format_error(400, str(e))


@api.app_errorhandler(BadConfigurationException)
def bad_configuration_error_handler(e):
    return format_error(400, str(e))


@api.app_errorhandler(AlreadyExistError)
def already_exists_error_handler(e):
    return format_controller_error(e), 409


@api.app_errorhandler(RequirementsNotSatisfiedError)
def requirements_error_handler(e):
    return format_controller_error(e), 409


@api.app_errorhandler(400)
def bad_request_handler(e):
    return format_error(400, "The server did not understand your request")


@api.app_errorhandler(401)
def unauthorized_handler(e):
    return format_error(401, "Could not verify your access level for that URL")


@api.app_errorhandler(403)
def forbidden_handler(e):
    return format_error(
        403, "You do not have the required permissions for that resource"
    )


@api.app_errorhandler(404)
def not_found_handler(e):
    return format_error(404, "The requested resource could not be found")


@api.app_errorhandler(405)
def method_not_allowed_handler(e):
    return format_error(405, "The method is not allowed for the requested URL")


@api.app_errorhandler(500)
def internal_server_error_handler(e):
    return format_error(
        500,
        "The server has either erred or is incapable "
        "of performing the requested operation",
    )

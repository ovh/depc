"""Rename check parameters

Revision ID: 88c2ab34728c
Revises: d2dc7ff020a0
Create Date: 2019-06-28 11:42:47.081483

"""
from sqlalchemy.exc import ProgrammingError

from depc.extensions import db
from depc.models.checks import Check


# revision identifiers, used by Alembic.
revision = "88c2ab34728c"
down_revision = "d2dc7ff020a0"
branch_labels = None
depends_on = None


KEYS_MAPPING = {"Fake": "metric", "OpenTSDB": "query", "WarpScript": "script"}


def upgrade():
    """
    This code upgrades the format of the checks data, not the schema
    itself. We need to verify if we're in a fresh DepC installation or
    if it's a DepC version upgrade.
    """
    try:
        checks = Check.query.all()

    # Handles the 'relation "checks" does not exist' error
    except ProgrammingError:
        return

    for check in checks:
        query = check.parameters[KEYS_MAPPING[check.source.plugin]]

        if check.type == "Threshold":
            threshold = check.parameters["threshold"]
        else:
            threshold = "{}:{}".format(
                check.parameters["bottom_threshold"], check.parameters["top_threshold"]
            )

        params = {"query": query, "threshold": threshold}
        check.parameters = params
    db.session.commit()


def downgrade():
    checks = Check.query.all()
    for check in checks:
        query = check.parameters["query"]
        params = {KEYS_MAPPING[check.source.plugin]: query}

        if check.type == "Threshold":
            params["threshold"] = check.parameters["threshold"]
        else:
            params["bottom_threshold"], params["top_threshold"] = check.parameters[
                "threshold"
            ].split(":")

        check.parameters = params
    db.session.commit()

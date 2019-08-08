import os

from depc import create_app
from depc.utils.neo4j import get_session


app = create_app(environment=os.getenv("DEPC_ENV") or "dev")

with app.app_context():
    neo_session = get_session()

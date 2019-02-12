import os

from depc import create_app


app = create_app(environment=os.getenv("DEPC_ENV") or "dev")

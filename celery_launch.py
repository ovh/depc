# -*- coding: utf8 -*-

import os

from depc import create_app
from depc.extensions import cel


app = create_app(
    os.getenv('DEPC_ENV') or 'default'
)
app.app_context().push()

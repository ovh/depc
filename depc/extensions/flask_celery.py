from celery import Celery


class FlaskCelery(Celery):
    def __init__(self, *args, **kwargs):

        super(FlaskCelery, self).__init__(*args, **kwargs)
        if "app" in kwargs:
            self.init_app(kwargs["app"])

    def init_app(self, app):
        self.app = app
        self.conf.update(app.config.get("CELERY_CONF", {}))

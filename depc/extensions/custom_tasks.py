from celery import Task
from celery.exceptions import Retry
from celery.utils.log import get_task_logger


class TaskWithLogger(Task):
    def run(self, *args, **kwargs):
        super(TaskWithLogger, self).run(*args, **kwargs)

    @property
    def logger(self):
        logger = get_task_logger(self.task_name)
        return logger

    @property
    def task_name(self):
        return "{}[{}]".format(self.name, self.request.id)

    @staticmethod
    def backoff(attempts):
        """Return a backoff delay, in seconds, given a number of
        attempts.

        The delay is logarithmic with the number of attempts:
        6, 17, 24, 29, 34, 37, 40, 42, 44, 47...

        """
        import math

        return int(10 * math.log((attempts + 2) * (attempts + 1)))

    def __call__(self, *args, **kwargs):
        from depc.extensions import db, cel
        from depc.tasks import UnrecoverableError, RevokeChain

        try:
            db.session.rollback()
            return super().__call__(*args, **kwargs)
        except (UnrecoverableError, RevokeChain, Retry):
            raise
        except Exception as error:
            if "CELERY_ALWAYS_EAGER" in cel.conf and cel.conf["CELERY_ALWAYS_EAGER"]:
                raise
            self.retry(countdown=self.backoff(self.request.retries), exc=error)
        finally:
            db.session.rollback()

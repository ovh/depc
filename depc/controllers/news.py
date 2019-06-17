from flask_login import current_user

from depc.controllers import Controller
from depc.extensions import db
from depc.models.news import News


class NewsController(Controller):

    model_cls = News

    @classmethod
    def list(cls, limit=None, unread=False):
        news = cls._list(order_by="created_at", reverse=True)

        # Select news unread by current user
        if unread:
            news = [n for n in news if n not in current_user.news]

        # If limit is specified
        try:
            if limit and int(limit) <= len(news):
                news = news[: int(limit)]
        except ValueError:
            pass

        return [cls.resource_to_dict(n) for n in news]

    @classmethod
    def get(cls, *args, **kwargs):
        news = cls._get(*args, **kwargs)

        if current_user not in news.users:
            news.users.append(current_user)
            db.session.add(news)
            db.session.commit()

        return cls.resource_to_dict(news)

    @classmethod
    def clear(cls):
        current_user.news = cls._list()
        db.session.add(current_user)
        db.session.commit()
        return {}

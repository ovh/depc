import sqlalchemy.exc
from loguru import logger

from depc.extensions import cel, db
from depc.utils import is_uuid


class ControllerError(Exception):
    def __init__(self, message, context=None):
        self.context = context or {}
        self.message = message.format(**self.context)

    def __str__(self):
        return self.message


class NotFoundError(ControllerError):
    pass


class AlreadyExistError(ControllerError):
    pass


class RequirementsNotSatisfiedError(ControllerError):
    pass


class IntegrityError(ControllerError):
    pass


class Controller(object):

    model_cls = None
    hidden_attributes = ()

    @classmethod
    def resource_to_dict(cls, obj, blacklist=False):
        d = obj.to_dict()
        if blacklist:
            d = {k: v for k, v in d.items() if k not in cls.hidden_attributes}
        return d

    @classmethod
    def _check_object(cls, obj):
        pass

    @classmethod
    def handle_integrity_error(cls, obj, error):
        raise error

    @classmethod
    def _join_to(cls, query, object_class):
        raise NotImplementedError(
            "Undefined join for {cls} and {class}",
            {"cls": cls.model_cls.__name__, "class": object_class.__name__},
        )

    @classmethod
    def schedule_task(cls, task_func, *args, **kwargs):
        task_result = task_func.delay(*args, **kwargs)
        if cel.conf.CELERY_ALWAYS_EAGER:
            # Tasks are already executed
            return []
        logger.info(
            "Scheduled async task {} with args {} {}".format(
                task_func.name, args, kwargs
            )
        )
        return [task_result.id]

    @classmethod
    def schedule_chain(cls, name, chain):
        logger.info("Scheduled async chain {}".format(name))
        chain_result = chain()
        if cel.conf.CELERY_ALWAYS_EAGER:
            # Tasks are already executed
            return []
        return [chain_result.id]

    @classmethod
    def _get_model_class_by_name(cls, class_name, parent_class=db.Model):
        for model in parent_class.__subclasses__():
            if model.__name__ == class_name:
                return model
            result = None
            try:
                result = cls._get_model_class_by_name(class_name, model)
            except NotImplementedError:
                pass
            if result is not None:
                return result
        raise NotImplementedError("{class} is undefined", {"class": class_name})

    @classmethod
    def _query(
        cls,
        filters=None,
        with_lock=False,
        single=True,
        limit=None,
        order_by=None,
        reverse=False,
    ):
        err = NotFoundError("Could not find resource")

        if filters is None:
            filters = {}

        query = cls.model_cls.query
        for class_name, class_filters in filters.items():
            class_object = cls._get_model_class_by_name(class_name)
            if class_object != cls.model_cls:
                query = cls._join_to(query, class_object)
            for filter_attr, filter_value in class_filters.items():
                if filter_attr == "id" and not is_uuid(filter_value):
                    raise err
                if isinstance(filter_value, list):
                    query = query.filter(
                        getattr(class_object, filter_attr).in_(filter_value)
                    )
                else:
                    query = query.filter(
                        getattr(class_object, filter_attr) == (filter_value)
                    )

        if with_lock:
            query = query.with_lockmode("update")

        if single:
            objs = query.first()
        else:
            if order_by:
                order_attribute = getattr(cls.model_cls, order_by)
            else:
                order_attribute = cls.model_cls.created_at
            query = query.order_by(
                order_attribute.desc() if reverse else order_attribute
            )
            if limit:
                query = query.limit(limit)
            objs = query.all()

        if objs is None:
            raise err

        return objs

    @classmethod
    def _list(
        cls, filters=None, order_by=None, limit=None, reverse=None, blacklist=False
    ):
        objs = cls._query(
            filters=filters,
            single=False,
            order_by=order_by,
            limit=limit,
            reverse=reverse,
        )
        return objs

    @classmethod
    def list(
        cls, filters=None, order_by=None, limit=None, reverse=None, blacklist=False
    ):
        """Fetch a list or resources

        Additional filters on model can be given to reduce the list of results
        """
        objs = cls._list(filters, order_by, limit, reverse, blacklist)
        return [cls.resource_to_dict(o, blacklist=blacklist) for o in objs]

    @classmethod
    def get(cls, filters, blacklist=False):
        obj = cls._get(filters)
        return cls.resource_to_dict(obj, blacklist=blacklist)

    @classmethod
    def _get(cls, filters):
        obj = cls._query(filters, single=True)
        return obj

    @classmethod
    def create(cls, data, commit=True):
        obj = cls._create(data, commit)
        return cls.resource_to_dict(obj)

    @classmethod
    def _create(cls, data, commit=True):
        cls.before_data_load(data)
        obj = cls.model_cls(**data)
        cls._check_object(obj)
        try:
            obj.check_integrity()
        except Exception as e:
            raise IntegrityError(str(e))

        cls.before_create(obj)
        db.session.add(obj)
        if commit:
            try:
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as error:
                cls.handle_integrity_error(obj, error)
                raise error  # Raised again if no error raised in the handler.
            logger.info("Created new {} {}".format(cls.model_cls.__name__, obj.id))
            cls.after_create(obj)
        else:
            logger.debug("Created new uncommitted {}".format(cls.model_cls.__name__))
        return obj

    @classmethod
    def create_if_not_exist(cls, *args, **kwargs):
        obj = cls._create_if_not_exist(*args, **kwargs)
        return cls.resource_to_dict(obj)

    @classmethod
    def _create_if_not_exist(cls, *args, **kwargs):
        data = kwargs.get("data", args[0] if args else None)
        try:
            object = cls._query(filters={cls.model_cls.__name__: data}, single=True)
        except NotFoundError:
            return cls._create(*args, **kwargs)
        return object

    @classmethod
    def create_many(cls, *args, **kwargs):
        objs = cls._create_many(*args, **kwargs)
        return [cls.resource_to_dict(o) for o in objs]

    @classmethod
    def _create_many(cls, data):
        """
        Create multi objects from list of data
        Warning: Lot of thing can append if object no commit use with caution
        """
        objs = []
        for obj_data in data:
            obj = cls._create(obj_data, commit=False)
            db.session.add(obj)
            # Flush to push update in PG transaction for future sql request
            db.session.flush()
            objs.append(obj)
        db.session.commit()
        for obj in objs:
            cls.after_create(obj)
        return objs

    @classmethod
    def update(cls, data, filters):
        obj = cls._update(data, filters)
        return cls.resource_to_dict(obj)

    @classmethod
    def _update(cls, data, filters):
        obj = cls._query(filters, single=True)
        cls.before_data_load(data)
        for key, value in data.items():
            setattr(obj, key, value)

        cls._check_object(obj)
        try:
            obj.check_integrity()
        except Exception as e:
            raise IntegrityError(str(e))
        try:
            cls.before_update(obj)
        except Exception:
            db.session.rollback()
            raise
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as error:
            cls.handle_integrity_error(obj, error)
            raise error  # Raised again if no error raised in the handler.
        cls.after_update(obj)
        logger.info("Updated {} {}".format(cls.model_cls.__name__, obj.id))
        return obj

    @classmethod
    def delete(cls, filters):
        return cls._delete(filters)

    @classmethod
    def _delete(cls, filters):
        """
        Delete specific object
        :return dict: deleted object dict
        """
        obj = cls._query(filters)
        obj_dict = cls.resource_to_dict(obj)
        cls.before_delete(obj)
        db.session.delete(obj)
        try:
            db.session.commit()
        except sqlalchemy.exc.IntegrityError as error:
            cls.handle_integrity_error(obj, error)
            raise error  # Raised again if no error raised in the handler.
        cls.after_delete(obj)
        return obj_dict

    @classmethod
    def before_update(cls, obj):
        pass

    @classmethod
    def after_update(cls, obj):
        pass

    @classmethod
    def before_create(cls, obj):
        pass

    @classmethod
    def after_create(cls, obj):
        pass

    @classmethod
    def before_delete(cls, obj):
        pass

    @classmethod
    def after_delete(cls, obj):
        pass

    @classmethod
    def before_data_load(cls, data):
        pass

    @classmethod
    def check_valid_period(cls, start, end):
        if not (start and end):
            raise IntegrityError("start and end params must be present")
        try:
            start = int(start)
            end = int(end)
        except ValueError:
            raise IntegrityError("start and end params must be timestamps")

        if start > end:
            raise IntegrityError(
                "start param ({0}) must be lower than end ({1})".format(start, end)
            )

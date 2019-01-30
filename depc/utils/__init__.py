import uuid

import arrow


def is_uuid(data):
    """Check is data is a valid uuid. If data is a list,
    checks if all elements of the list are valid uuids"""
    temp = [data] if not isinstance(data, list) else data
    for i in temp:
        try:
            uuid.UUID(str(i), version=4)
        except ValueError:
            return False
    return True


def to_list(obj):
    """ Return a list containing obj if obj is not already an iterable"""
    try:
        iter(obj)
        return obj
    except TypeError:
        return [obj]


def get_start_end_ts(day=None):
    if not day:
        # yesterday at midnight
        date = arrow.utcnow().shift(days=-1).floor("day")
    else:
        # given day, at midnight (arrow works in UTC by default)
        date = arrow.get(day)

    start = date.timestamp
    end = date.ceil("day").timestamp

    return start, end

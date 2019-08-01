from flask import current_app as app
from neo4j.v1 import GraphDatabase as BoltGraphDatabase
from neo4jrestclient.client import GraphDatabase
from neo4jrestclient.query import Q


# TODO: we must remove the rest client and just use the bolt client
class Neo4jClient:
    def __init__(self, url=None, username=None, password=None):
        if url is None:
            url = app.config["NEO4J"]["url"]
        if username is None:
            username = app.config["NEO4J"]["username"]
        if password is None:
            password = app.config["NEO4J"]["password"]

        self.gdb = GraphDatabase(url=url, username=username, password=password)

    def get_node_by_property(self, label, property, value):
        labels = self.gdb.labels.get(label)
        lookup = Q(property, contains=value)

        elements = labels.filter(lookup).elements
        data = [dict(elt.items()) for elt in elements]

        return data

    def query(self, cypher, returns=None, data_contents=False, params={}):
        data = {
            "q": cypher,
            "returns": returns,
            "data_contents": data_contents,
            "params": params,
        }

        results = self.gdb.query(**data)

        return results


def is_active_node(start, end, node):
    """This function checks the end of life of a node"""
    return (start <= node.get("from", 0) <= end) or (
        node.get("from", 0) <= start <= node.get("to", float("inf"))
    )


def is_node_active_at_timestamp(node, ts):
    """Check if a node is active at a given timestamp"""
    return node.get("from", 0) <= ts <= node.get("to", float("inf"))


def compute_active_periods(start, end, periods):
    active_periods = {}

    def _add_period(p_start, p_end):
        if end >= p_start and start <= p_end:
            if p_start < start:
                active_periods[start] = True
            else:
                active_periods[p_start] = True

            # WARNING : if p_end == start the key is rewritten
            # Example: start = 1545091200 and periods = [1545090000, 1545091200]
            active_periods[p_end] = False

    # Iterate over an even list of timestamps
    def _iterate_over_periods(list_ts):
        iter_periods = iter(list_ts)
        for p in iter_periods:
            _add_period(p, next(iter_periods))

    length = len(periods)

    if length == 1:
        ts = periods[0]
        if end >= ts:
            return {ts: True}
        return {}

    if length % 2 == 0:
        _iterate_over_periods(periods)
    else:
        last_ts = periods[-1]
        _iterate_over_periods(periods[:-1])
        _add_period(last_ts, end)

    return active_periods


def has_active_relationship(start, end, periods):
    active_periods = compute_active_periods(start, end, periods)
    return len(active_periods) > 0


def is_relationship_active_at_timestamp(relationship, ts):
    """Check if a relationship is active at a given timestamp"""
    def _check_period(p_start, p_end):
        """Check if a given timestamp is inside a period"""
        if p_start <= ts <= p_end:
            return True
        return False

    # Iterate over an even list of timestamps
    def _iterate_over_periods(periods_ts_list):
        """Check if a given timestamp is inside one of the periods of a relationship"""
        iter_periods = iter(periods_ts_list)
        for p in iter_periods:
            if _check_period(p, next(iter_periods)):
                return True
        return False

    relationship_periods = relationship.get("periods", [])

    # If no periods are found, consider the relationship active
    if len(relationship_periods) == 0:
        return True

    # If we only have one timestamp inside the periods, that means that the period is started without an end,
    # which means we just need to check if the given timestamp is after this period start or not
    if len(relationship_periods) == 1:
        if ts >= relationship_periods[0]:
            return True
        return False

    if len(relationship_periods) % 2 == 0:
        # If we have an even number of periods, we have an array of finished periods and we need to
        # iterate over them to determine if the given timestamp is inside one of them
        return _iterate_over_periods(relationship_periods)
    else:
        # If we have an odd number of periods, we have an array of finished period and a last period started
        # without an end, so we need to check first if the timestamp is after the last period without and end
        # and if not, iterate over the other periods
        last_period_ts = relationship_periods[-1]
        if ts >= last_period_ts:
            return True
        return _iterate_over_periods(relationship_periods[:-1])


def get_records(query, params={}):
    config = app.config["NEO4J"]

    driver = BoltGraphDatabase.driver(
        config["uri"], auth=(config["username"], config["password"])
    )
    session = driver.session()

    return session.read_transaction(lambda tx: tx.run(query, params))


def set_records(query, params={}):
    config = app.config["NEO4J"]

    driver = BoltGraphDatabase.driver(
        config["uri"], auth=(config["username"], config["password"])
    )
    session = driver.session()

    return session.write_transaction(lambda tx: tx.run(query, params))

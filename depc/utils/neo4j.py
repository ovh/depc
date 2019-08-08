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


def get_session():
    config = app.config["NEO4J"]

    driver = BoltGraphDatabase.driver(
        config["uri"], auth=(config["username"], config["password"])
    )
    return driver.session()


def get_records(query, params={}, session=None):
    if not session:
        session = get_session()
    return session.read_transaction(lambda tx: tx.run(query, params))


def set_records(query, params={}, session=None):
    if not session:
        session = get_session()
    return session.write_transaction(lambda tx: tx.run(query, params))

import os

from neo4j.v1 import GraphDatabase

from depc import create_app

app = create_app(environment=os.getenv("DEPC_ENV") or "default")


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


def get_records(query, params={}):
    config = app.config["NEO4J"]

    driver = GraphDatabase.driver(
        config["uri"], auth=(config["username"], config["password"])
    )
    session = driver.session()

    return session.read_transaction(lambda tx: tx.run(query, params))

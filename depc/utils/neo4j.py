from flask import current_app as app
from neo4jrestclient.client import GraphDatabase
from neo4jrestclient.query import Q


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

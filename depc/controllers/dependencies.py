import re

import arrow
from neo4jrestclient.constants import DATA_GRAPH
from neo4jrestclient.exceptions import TransactionException
from neo4jrestclient import client

from depc.controllers import Controller, NotFoundError, RequirementsNotSatisfiedError
from depc.controllers.configs import ConfigController
from depc.controllers.teams import TeamController
from depc.utils.neo4j import (
    Neo4jClient,
    get_records,
    is_active_node,
    has_active_relationship,
)


class DependenciesController(Controller):
    @classmethod
    def get_labels(cls, team_id):
        """
        This function returns the list of labels for a team. The labels can be
        found in 2 places : in the configuration or directly in Neo4j.

        Having a label in Neo4j does not mean it's present in the config, and
        having a label in the config does not mean it has been created in Neo4j.
        """
        team = TeamController._get({"Team": {"id": team_id}})

        # Get labels per team
        neo = Neo4jClient()
        query = (
            "CALL db.labels() YIELD label "
            "WITH split(label, '_')[0] AS Team, split(label, '_')[1] AS Label "
            "RETURN Team, collect(Label) AS Labels "
            "ORDER BY Team"
        )
        results = neo.query(query, returns=(str, list))

        # Get the label for the current team
        labels_per_teams = {r[0]: r[1] for r in results}

        # Pick the wanted team's labels
        team_labels = labels_per_teams.get(team.kafka_topic, [])

        # Get the number of nodes per label
        labels = {}
        if team_labels:
            query = cls._build_query_count_nodes(team.kafka_topic, team_labels)
            results = neo.query(query, returns=(str, int))

            # Merge the Neo4j and DB labels
            labels = {
                r[0]: {"name": r[0], "nodes_count": r[1], "qos_query": None}
                for r in results
            }

        # No config: return the list of labels
        try:
            config = ConfigController.get_current_config(team_id)
        except NotFoundError:
            return list(labels.values())

        # Add the QoS query for each label
        qos_queries = {l: d["qos"] for l, d in config["data"].items()}
        for label, query in qos_queries.items():
            if label not in labels:
                labels[label] = {"name": label, "nodes_count": 0}
            labels[label]["qos_query"] = query

        return list(labels.values())

    @classmethod
    def get_label_nodes(cls, team_id, label, name=None, limit=None, random=False):
        team = TeamController._get({"Team": {"id": team_id}})

        neo = Neo4jClient()
        query = cls._build_query_nodes(team.kafka_topic, label, random, name, limit)

        results = neo.query(query, returns=(str,))
        return [r[0] for r in results]

    @classmethod
    def get_label_node(cls, team_id, label, node):
        team = TeamController._get({"Team": {"id": team_id}})

        neo = Neo4jClient()
        query = "MATCH(n:{0}_{1}{{name: '{2}'}}) RETURN n".format(
            team.kafka_topic, label, node
        )
        result = neo.query(query)

        try:
            data = list(result)[0][0]["data"]
        except IndexError:
            raise NotFoundError("Node {} does not exist".format(node))

        return data

    @classmethod
    def count_node_dependencies(cls, team_id, label, node):
        team = TeamController._get({"Team": {"id": team_id}})

        neo = Neo4jClient()
        query = (
            "MATCH(n:{0}_{1}{{name: '{2}'}}) "
            "OPTIONAL MATCH (n)-[:DEPENDS_ON]->(m) "
            "RETURN count(m)"
        ).format(team.kafka_topic, label, node)
        sequence = neo.query(query, data_contents=DATA_GRAPH)

        return {"count": sequence[0][0]}

    @classmethod
    def get_node_dependencies(
        cls,
        team_id,
        label,
        node,
        day=None,
        filter_on_config=False,
        include_inactive=False,
        display_impacted=False,
    ):
        topic = TeamController._get({"Team": {"id": team_id}}).kafka_topic
        query = cls._build_dependencies_query(
            team_id, topic, label, node, filter_on_config, display_impacted
        )
        dependencies = {"dependencies": {}, "graph": {"nodes": [], "relationships": []}}
        records = get_records(query)

        # Loop on all relationships
        for idx, record in enumerate(records):

            # Handle the main node
            if idx == 0:
                node = record.get("n")
                title = list(node.labels)[0][len(topic) + 1 :]

                if title not in dependencies["dependencies"]:
                    dependencies["dependencies"][title] = []
                dependencies["dependencies"][title].append(dict(node.items()))

                dependencies["graph"]["nodes"].append(
                    {"id": node.id, "label": dict(node.items())["name"], "title": title}
                )

            # Handle the relationship
            rel = record.get("r")
            if not rel:
                continue

            # Check inactive nodes
            if display_impacted:
                start_node = rel.end_node
                end_node = rel.start_node
            else:
                start_node = rel.start_node
                end_node = rel.end_node

            start = arrow.get(day, "YYYY-MM-DD").floor("day").timestamp
            end = arrow.get(day, "YYYY-MM-DD").ceil("day").timestamp

            if (not is_active_node(start, end, end_node)) or (
                not has_active_relationship(start, end, rel.get("periods"))
            ):
                if not include_inactive:
                    continue
                else:
                    setattr(end_node, "inactive", True)

            # The label is 'acme_Mylabel', we just want 'Mylabel'
            title = list(end_node.labels)[0][len(topic) + 1 :]

            if title not in dependencies["dependencies"]:
                dependencies["dependencies"][title] = []
            dependencies["dependencies"][title].append(
                {
                    **dict(end_node.items()),
                    **{
                        "periods": list(rel.get("periods")),
                        "inactive": getattr(end_node, "inactive", False),
                    },
                }
            )

            dependencies["graph"]["nodes"].append(
                {
                    "id": end_node.id,
                    "label": dict(end_node.items())["name"],
                    "title": title,
                }
            )

            dependencies["graph"]["relationships"].append(
                {
                    "id": rel.id,
                    "from": end_node.id if display_impacted else start_node.id,
                    "to": start_node.id if display_impacted else end_node.id,
                    "arrows": "to",
                    "periods": list(rel.get("periods")),
                }
            )

        return dependencies

    @classmethod
    def delete_node(cls, team_id, label, node, detach=False):
        team = TeamController._get({"Team": {"id": team_id}})
        neo = Neo4jClient()
        query = 'MATCH(n:{topic}_{label}{{name: "{name}"}})'.format(
            topic=team.kafka_topic, label=label, name=node
        )

        # First we check if the node has dependencies
        has_deps = query + "-[r:DEPENDS_ON]->() RETURN count(r)"
        count = neo.query(has_deps, returns=(int,))[0][0]  # return is weird : [[100]]

        if count and not detach:
            msg = (
                "Can not delete node {node} because it still has {count} relationships"
            )
            raise RequirementsNotSatisfiedError(msg.format(node=node, count=count))

        # We can delete the node and its relationships
        query += " DETACH DELETE n"

        try:
            # Neo4j returns nothing when deleting a node
            neo.query(query)
        except TransactionException as e:
            raise RequirementsNotSatisfiedError(str(e))

        return {}

    @classmethod
    def _build_query_count_nodes(cls, topic, labels):
        query = (
            "MATCH (n:{team}_{label}) "
            "WITH '{label}' AS Label, count(n) AS Count "
            "RETURN Label, Count "
        ).format(team=topic, label=labels[0])

        for label in labels[1:]:
            query += (
                "UNION MATCH (n:{team}_{label}) "
                "WITH '{label}' AS Label, count(n) AS Count "
                "RETURN Label, Count "
            ).format(team=topic, label=label)

        return query

    @classmethod
    def _build_query_nodes(cls, topic, label, random=None, name=None, limit=None):
        query = "MATCH (n:{}_{}) WITH n".format(topic, label)

        # Randomize the nodes
        if random:
            query += ", rand() as r ORDER BY r"

        # Filter by name
        if name:
            query += " WHERE n.name CONTAINS '{0}'".format(name)

        # Only return the name of the nodes
        query += " RETURN n.name"

        try:
            limit = int(limit)
            query += " LIMIT {0}".format(limit)
        except (TypeError, ValueError):
            pass

        return query

    @classmethod
    def _build_dependencies_query(
        cls, team_id, topic, label, node, filter_on_config=False, impacted=False
    ):
        """Build a Cypher query based on given parameters."""
        where = ""
        order = "(n)<-[r]-(m)" if impacted else "(n)-[r]->(m)"
        query = (
            "MATCH(n:{topic}_{label}{{name: '{name}'}}) "
            "OPTIONAL MATCH {order} {where}"
            "RETURN n,r,m ORDER BY m.name LIMIT 10"
        )

        # Filter the dependencies using the labels declared in the configuration
        if filter_on_config:
            label_config = ConfigController.get_label_config(team_id, label)
            regex = r"^.*(\[[A-Za-z]+(, [A-Za-z]+)*?\])$"

            match = re.search(regex, label_config["qos"])
            if match:
                deps = match.group(1)[1:-1].split(", ")
                where += "WHERE '{}_{}' IN LABELS(m) ".format(topic, deps[0])

                for dep in deps[1:]:
                    where += "OR '{}_{}' IN LABELS(m) ".format(topic, dep)

        return query.format(
            where=where, order=order, topic=topic, label=label, name=node
        )

    @classmethod
    def get_impacted_nodes(cls, team_id, label, node, impacted_label=None):
        team = TeamController._get({"Team": {"id": team_id}})

        neo = Neo4jClient()
        query = "MATCH (n:{topic}_{impacted_label})-[*]->(:{topic}_{label}{{name: '{name}'}}) RETURN n".format(
            topic=team.kafka_topic, impacted_label=impacted_label, label=label, name=node
        )

        impacted_nodes = []
        results = neo.query(query, returns=client.Node)
        for result in results:
            impacted_nodes.append(result[0]['name'])
        return impacted_nodes

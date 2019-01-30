import re

from neo4jrestclient.constants import DATA_GRAPH
from neo4jrestclient.exceptions import TransactionException

from depc.controllers import Controller, NotFoundError, RequirementsNotSatisfiedError
from depc.controllers.configs import ConfigController
from depc.controllers.teams import TeamController
from depc.utils.neo4j import Neo4jClient


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
        query = """CALL db.labels() YIELD label
        WITH split(label, '_')[0] AS Team, split(label, '_')[1] AS Label
        RETURN Team, collect(Label) AS Labels
        ORDER BY Team"""
        results = neo.query(query, returns=(str, list))

        # Get the label for the current team
        labels_per_teams = {r[0]: r[1] for r in results}

        # Pick the wanted team's labels
        team_labels = labels_per_teams.get(team.kafka_topic, [])

        # Construct the cypher to get the number of nodes per label
        # TODO : add cache for this feature
        labels = {}
        if team_labels:
            query = (
                "MATCH (n:{team}_{label}) "
                'WITH "{label}" AS Label, count(n) AS Count '
                "RETURN Label, Count"
            )
            query = query.format(team=team.kafka_topic, label=team_labels[0])

            for label in team_labels[1:]:
                union = (
                    "\nUNION MATCH (n:{team}_{label}) "
                    'WITH "{label}" AS Label, count(n) AS Count '
                    "RETURN Label, Count"
                )
                query += union.format(team=team.kafka_topic, label=label)

            results = neo.query(query, returns=(str, int))

            # Merge the Neo4j and DB labels
            labels = {
                r[0]: {"name": r[0], "nodes_count": r[1], "qos_query": None}
                for r in results
            }
        try:
            config = ConfigController.get_current_config(team_id)
        except NotFoundError:
            return list(labels.values())

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
        query = "MATCH (n:{}_{}) WITH n".format(team.kafka_topic, label)

        if random:
            query += ", rand() as r ORDER BY r"

        if name:
            query += " WHERE n.name CONTAINS '{0}'".format(name)

        query += " RETURN distinct(n.name)"

        try:
            limit = int(limit)
            query += " LIMIT {0}".format(limit)
        except (TypeError, ValueError):
            pass

        results = neo.query(query, returns=(str,))
        return [r[0] for r in results]

    @classmethod
    def count_node_dependencies(cls, team_id, label, node):
        team = TeamController._get({"Team": {"id": team_id}})

        neo = Neo4jClient()
        query = """
        MATCH(n:{0}_{1}{{name: "{2}"}})
        OPTIONAL MATCH (n)-[:DEPENDS_ON]->(m)
        RETURN count(m)
        """.format(
            team.kafka_topic, label, node
        )
        sequence = neo.query(query, data_contents=DATA_GRAPH)

        return {"count": sequence[0][0]}

    @classmethod
    def get_node_dependencies(cls, team_id, label, node, filter_on_config=False):
        team = TeamController._get({"Team": {"id": team_id}})
        query = """
        MATCH(n:{topic}_{label}{{name: "{name}"}})
        OPTIONAL MATCH (n)-[r]->(m) {where}
        RETURN n,r,m
        ORDER BY m.name LIMIT 10
        """

        # Filter the dependencies with the labels declared in the configuration
        where = ""
        if filter_on_config:
            label_config = ConfigController.get_label_config(team_id, label)
            regex = r"^.*(\[[A-Za-z]+(, [A-Za-z]+)*?\])$"
            match = re.search(regex, label_config["qos"])
            if match:
                deps = match.group(1)[1:-1].split(", ")
                where += "WHERE '{}_{}' IN LABELS(m)".format(team.kafka_topic, deps[0])
                for dep in deps[1:]:
                    where += " OR '{}_{}' IN LABELS(m)".format(team.kafka_topic, dep)

        neo = Neo4jClient()
        query = query.format(
            topic=team.kafka_topic, label=label, name=node, where=where
        )
        sequence = neo.query(query, data_contents=DATA_GRAPH)

        dependencies = {"dependencies": {}, "graph": {"nodes": [], "relationships": []}}

        if sequence.graph:
            for g in sequence.graph:

                # Handle the nodes
                for node in g["nodes"]:
                    title = node["labels"][0][len(team.kafka_topic) + 1 :]
                    if title not in dependencies["dependencies"]:
                        dependencies["dependencies"][title] = []

                    # Id is required to make data unique later
                    node["properties"]["id"] = node["id"]
                    dependencies["dependencies"][title].append(node["properties"])

                    # Add the node data in the whole graph
                    dependencies["graph"]["nodes"].append(
                        {
                            "id": node["id"],
                            "label": node["properties"].get("name", "unknown"),
                            "title": title,
                        }
                    )

                # Handle the relationships
                for rel in g["relationships"]:
                    dependencies["graph"]["relationships"].append(
                        {
                            "id": rel["id"],
                            "from": rel["startNode"],
                            "to": rel["endNode"],
                            "arrows": "to",
                        }
                    )

        dependencies = cls.make_unique(dependencies)
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
    def make_unique(cls, deps):
        """This function takes a dict and returns the unique dependencies."""

        # Dependencies
        for dep in deps["dependencies"]:
            unique = {v["id"]: v for v in deps["dependencies"][dep]}.values()
            deps["dependencies"][dep] = list(unique)

        # Nodes
        unique = {v["id"]: v for v in deps["graph"]["nodes"]}.values()
        deps["graph"]["nodes"] = list(unique)

        # Relationships
        unique = {v["id"]: v for v in deps["graph"]["relationships"]}.values()
        deps["graph"]["relationships"] = list(unique)

        return deps

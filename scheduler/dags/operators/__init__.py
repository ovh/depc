import json
import logging
import os
import time
import uuid

import arrow
import collections
from airflow.models import BaseOperator

from depc.utils.neo4j import is_active_node, get_records, has_active_relationship
from scheduler.dags.decoder import BoolsDpsDecoder

logger = logging.getLogger(__name__)


class QosOperator(BaseOperator):
    template_fields = tuple()

    def __init__(self, params, *args, **kwargs):
        super(QosOperator, self).__init__(*args, **kwargs)
        self.app = params["app"]
        self.team = params["team"]
        self.label = params["label"]
        self.skip = params.get("skip")
        self.length = params.get("length")

        self.team_id = self.team["id"]
        self.team_name = self.team["name"]
        self.topic = self.team["topic"]
        self.schema = self.team["schema"]

    @staticmethod
    def lower(s):
        return "".join(e for e in s if e.isalnum()).lower()

    @staticmethod
    def format_metric(metric, ts, value, tags):
        tags = collections.OrderedDict(sorted(tags.items()))
        tags = ",".join(["{}={}".format(k, v) for k, v in tags.items()])

        return "{timestamp}// {metric}{{{tags}}} {value}".format(
            timestamp="{ts}000000".format(ts=ts), metric=metric, tags=tags, value=value
        )

    def write_metric_on_fs(self, metrics):
        with self.app.app_context():
            sources = self.app.config["BEAMIUM"]["source-dir"]

        def _write_on_fs(_filename, data):
            with open(_filename, mode="w", encoding="utf-8") as f:
                f.write(data)

        filename = "{path}/{id}-{ts}.metrics".format(
            path=sources[:-1] if sources.endswith("/") else sources,
            id=uuid.uuid4().hex,
            ts="{}000000".format(arrow.utcnow().timestamp),
        )
        if type(metrics) == list:
            # In some cases, Beamium can ingest the file before all metrics were written
            # and produces a corrupted file into the "sinks" folder.
            # That's why we use a temporary file to write multiple metrics first and then
            # rename this file into the right filename for Beamium.
            temporary_filename = "{}.tmp".format(filename)
            _write_on_fs(temporary_filename, "\n".join(metrics))
            os.rename(temporary_filename, filename)
        else:
            _write_on_fs(filename, metrics)

        self.log.info("Result written in {f}".format(f=filename))

        return filename

    def write_metric(self, metric, ts, value, tags):
        metric = self.format_metric(metric=metric, ts=ts, value=value, tags=tags)
        return self.write_metric_on_fs(metric)

    def write_metrics(self, metrics):
        return self.write_metric_on_fs(metrics)


class DependenciesOperator(QosOperator):
    def __init__(self, params, *args, **kwargs):
        super(DependenciesOperator, self).__init__(params, *args, **kwargs)
        self.type = params["type"]
        self.dependencies = params["dependencies"]

    def get_type(self):
        raise NotImplementedError()

    def compute_node_qos(self, data, start, end):
        raise NotImplementedError()

    def build_query(self):
        """
        This function build a Neo4j cypher according the dependencies of a label.

        For example the `Hosting` label with `Database`, `Filer` and
        `ClusterInfra` dependencies will build the following Cypher :

          MATCH (hosting:webhosting_Hosting)
          WITH hosting ORDER BY hosting.name SKIP X LIMIT Y
          OPTIONAL MATCH(hosting)-[hosting_database:DEPENDS_ON]->(database:webhosting_Database)
          OPTIONAL MATCH(hosting)-[hosting_filer:DEPENDS_ON]->(filer:webhosting_Filer)
          OPTIONAL MATCH(hosting)-[hosting_clusterinfra:DEPENDS_ON]->(clusterinfra:webhosting_ClusterInfra)
          WITH
            hosting,
            COLLECT(DISTINCT({node: database, rel: hosting_database})) AS database,
            COLLECT(DISTINCT({node: filer, rel: hosting_filer})) AS filer,
            COLLECT(DISTINCT({node: clusterinfra, rel: hosting_clusterinfra})) AS clusterinfra
          RETURN
            hosting,
            CASE WHEN database[0]['node'] IS NOT NULL THEN database ELSE NULL END AS database,
            CASE WHEN filer[0]['node'] IS NOT NULL THEN filer ELSE NULL END AS filer,
            CASE WHEN clusterinfra[0]['node'] IS NOT NULL THEN clusterinfra ELSE NULL END AS clusterinfra

        :return: a tuple containing the name of the main node, the name of the dependencies and the query
        """
        name = self.lower(self.label)
        deps = []

        query_tmpl = "MATCH ({name}:{label})".format(
            name=name, label="{}_{}".format(self.topic, self.label)
        )

        # Order and limit the main node
        query_tmpl += " WITH {name} ORDER BY {name}.name SKIP {skip} LIMIT {limit}".format(
            name=name, skip=self.skip, limit=int(self.length)
        )

        # Loop on each label and match them
        for dep in self.dependencies:
            dep_name = self.lower(dep)
            label_name = "{}_{}".format(self.topic, dep)
            rel_name = "{}_{}".format(name, dep_name)

            query_tmpl += " OPTIONAL MATCH({name})-[{rel}:DEPENDS_ON]->({dep_name}:{label})".format(
                name=name, rel=rel_name, dep_name=dep_name, label=label_name
            )
            deps.append({"label": label_name, "node": dep_name, "rel": rel_name})

        # Store the main node and their relationship
        query_tmpl += " WITH {name}".format(name=name)
        for dep in deps:
            query_tmpl += ", COLLECT(DISTINCT({{node: {node}, rel: {rel}}})) AS {node}".format(
                node=dep["node"], rel=dep["rel"]
            )

        # Return unique rows and filter them if no node exists
        query_tmpl += " RETURN {name}".format(name=name)
        for dep in deps:
            query_tmpl += ", CASE WHEN {node}[0]['node'] IS NOT NULL THEN {node} ELSE NULL END AS {node}".format(
                node=dep["node"]
            )

        return name, deps, query_tmpl

    def filter_records(self, start, end, records, name, dependencies):
        """
        This function transforms the data returned by Neo4j into a format we
        can use to search data in our TimeSeries database.

        We also take this opportunity to filter inactive nodes or nodes with
        inactive relationship.
        """
        data = {}
        for record in records:
            node = record.get(name)

            # Remove inactive nodes
            if not is_active_node(start, end, node):
                self.log.info(
                    "{node} is no longer active, skip it.".format(node=node["name"])
                )
                continue

            # Transform the records
            data[node["name"]] = []
            for dependency in dependencies:

                # For each dependency in this label
                for n in record.get(dependency["node"]) or []:

                    # Do not use inactive dependencies or dependencies with inactive relation
                    if not is_active_node(
                        start, end, n["node"]
                    ) or not has_active_relationship(start, end, n["rel"]["periods"]):
                        self.log.info(
                            "Dependency {node} is no longer active, skip it.".format(
                                node=n["node"]["name"]
                            )
                        )
                        continue

                    # This dependency can be used to compute the QOS of the main node
                    data[node["name"]].append(
                        {"label": dependency["label"], "name": n["node"]["name"]}
                    )

        # Remove nodes without any dependency
        data = {k: v for k, v in data.items() if v}

        return data

    def execute(self, context):
        from depc.extensions import redis_scheduler as redis
        from depc.utils import get_start_end_ts

        ds = context["ds"]
        start, end = get_start_end_ts(ds)
        name, dependencies, query = self.build_query()

        self.log.info(
            "[{team}/{label}] Fetching nodes and its dependencies using the following query : {query}".format(
                team=self.team_name, label=self.label, query=query
            )
        )

        # Retrieve the node and its dependencies
        start_time = time.time()
        with self.app.app_context():
            records = get_records(query)
        nodes = self.filter_records(
            start=start,
            end=end,
            records=[r for r in records],
            name=name,
            dependencies=dependencies,
        )

        # No node has dependency
        if not nodes:
            self.log.warning(
                "[{team}/{label}] No node has dependency.".format(
                    team=self.team_name, label=self.label
                )
            )
            return

        self.log.info(
            "[{team}/{label}] Nodes fetched in {t}s, processing it...".format(
                team=self.team_name,
                label=self.label,
                t=round(time.time() - start_time, 3),
            )
        )

        # Process the nodes and remove the archived ones
        start_time = time.time()

        msg = "[{team}/{label}] Processing done in {t}s, {count} nodes returned (from {begin} to {end})"
        self.log.info(
            msg.format(
                team=self.team_name,
                label=self.label,
                t=round(time.time() - start_time, 3),
                count=len(nodes),
                begin=list(nodes.keys())[0],
                end=list(nodes.keys())[-1],
            )
        )

        self.log.info(
            "[{team}/{label}] Computing the QOS for {count} nodes...".format(
                team=self.team_name, label=self.label, count=len(nodes)
            )
        )

        start_time = time.time()
        QOS = {}
        metrics = []
        nodes_without_qos = []
        idx = 0

        for node, deps in nodes.items():
            self.log.info(
                "[{team}/{label}] Fetching the QOS of {count} dependencies for {node}...".format(
                    team=self.team_name, label=self.label, count=len(deps), node=node
                )
            )

            node_deps = []
            for d in deps:
                dep_name = d["name"]
                dep_label = d["label"]

                # The label contains the topic but not the redis key
                dep = "{0}.{1}".format(dep_label.split("_")[1], dep_name)

                # It's the first time we see this dependency
                if dep not in QOS.keys():

                    # We retrieve its QOS in Redis
                    qos = redis.get(
                        "{ds}.{team}.{dep}.node".format(
                            ds=ds, team=self.team_name, dep=dep
                        )
                    )
                    if qos:
                        QOS[dep] = json.loads(qos.decode("utf-8"), cls=BoolsDpsDecoder)

                # Add the result of the dependencies for this node
                try:
                    node_deps.append(QOS[dep])
                except KeyError:
                    msg = (
                        "The QOS of {dep} is not available "
                        "(no data in any metric ?)".format(dep=dep_name)
                    )
                    logger.warning(msg)

            if node_deps:
                msg = (
                    "[{team}/{label}] Computing the QOS of {node} using a {type} "
                    "between {count} dependencies with valid QOS..."
                )
                self.log.info(
                    msg.format(
                        team=self.team_name,
                        label=self.label,
                        node=node,
                        type=self.type,
                        count=len(node_deps),
                    )
                )

                node_qos = self.compute_node_qos(data=node_deps, start=start, end=end)

                self.log.info(
                    "[{0}/{1}] The QOS of {2} is {3}%".format(
                        self.team_name, self.label, node, node_qos["qos"]
                    )
                )

                metrics.append(
                    self.format_metric(
                        metric="depc.qos.node",
                        ts=start,
                        value=node_qos["qos"],
                        tags={"label": self.label, "name": node, "team": self.team_id},
                    )
                )

                # Save it in redis for the average
                key = "{ds}.{team}.{label}".format(
                    ds=ds, team=self.team_name, label=self.label
                )
                redis.zadd("{}.sorted".format(key), node, node_qos["qos"])

                # Save information to reuse it later (`bools_dps` is used in
                # OperationOperator and `qos` is used in AggregationOperator)
                redis.set("{}.{}.node".format(key, node), json.dumps(node_qos))
            else:
                self.log.warning(
                    "[{team}/{label}] {node} has no dependency with QOS".format(
                        team=self.team_name, label=self.label, node=node
                    )
                )
                nodes_without_qos.append(node)

                # Add it in redis to compute some stats in AfterSubdagOperator
                redis.sadd(
                    "{ds}.{team}.{label}.noqos".format(
                        ds=ds, team=self.team_name, label=self.label
                    ),
                    node,
                )

            idx += 1
            if idx and idx % 1000 == 0:
                self.log.info(
                    "[{team}/{label}] {count} nodes processed in {time}s".format(
                        team=self.team_name,
                        label=self.label,
                        count=idx,
                        time=round(time.time() - start_time, 3),
                    )
                )

        self.log.info(
            "[{team}/{label}] The QOS of {count} nodes has been computed in {time}s".format(
                team=self.team_name,
                label=self.label,
                count=len(metrics),
                time=round(time.time() - start_time, 3),
            )
        )

        if nodes_without_qos:
            msg = "[{team}/{label}] The QOS could not be found for {count} nodes ({excerpt}, ...)"
            self.log.warning(
                msg.format(
                    team=self.team_name,
                    label=self.label,
                    count=len(nodes_without_qos),
                    excerpt=", ".join(nodes_without_qos[:5]),
                )
            )

        # Write metrics for Beamium
        if not metrics:
            self.log.warning(
                "[{team}/{label}] No QOS to save, chunk is finished.".format(
                    team=self.team_name, label=self.label
                )
            )
        else:
            self.write_metrics(metrics)


def delete_redis_avg(ds, **kwargs):
    """
    This tasks, launched before the chunks of a label, deletes the
    key in Redis used  to compute the label average.
    """
    from depc.extensions import redis_scheduler as redis

    app = kwargs["params"]["app"]
    key = "{ds}.{team}.{label}.sorted".format(
        ds=ds, team=kwargs["params"]["team"]["name"], label=kwargs["params"]["label"]
    )

    with app.app_context():
        logger.info("Deleting {0} key in redis...".format(key))
        redis.delete(key)

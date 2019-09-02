import time
import uuid
from collections import OrderedDict

import fastjsonschema
from kafka import KafkaConsumer, TopicPartition
from loguru import logger
from neo4j.exceptions import ServiceUnavailable
from neo4j.v1 import GraphDatabase

from consumer.kafka_consumer.utils import (
    validate_flat_message,
    validate_nested_message,
    NODE_TEMPLATE,
    REL_TEMPLATE,
)


class Neo4jBoltDriver(object):
    def __init__(self, conf):
        self.session = None
        self.driver = None
        self.uri = conf["uri"]
        self.auth = conf["auth"]
        self.encrypted = conf["encrypted"]
        self.trust = conf["trust"]

    def connect(self):
        self.driver = GraphDatabase.driver(
            uri=self.uri, auth=self.auth, encrypted=self.encrypted, trust=self.trust
        )
        self.session = self.driver.session()
        return self

    def exec_cypher(self, query, params):
        """Execute a query on Neo4j using the Bolt driver."""
        while True:
            try:
                logger.debug("Executing Cypher query...")
                with self.session.begin_transaction() as tx:
                    result = tx.run(query, params)
                    tx.success = True
                summary = result.consume()
                logger.debug("Finished to consume query result")
            except (ServiceUnavailable, OSError, ConnectionError) as e:
                logger.warning(
                    'Error requesting the Neo4j : "{}". Retrying in 10 seconds...'.format(
                        str(e)
                    )
                )
                time.sleep(10)
                try:
                    self.session = self.driver.session()
                except Exception as e:
                    logger.warning(
                        'Error creating the Neo4j driver session : "{}"...'.format(
                            str(e)
                        )
                    )
                continue
            else:
                return result, summary


def generate_batch_id():
    return uuid.uuid4().hex[:10]


def trigger_heartbeat(neo_driver):
    now = int(time.time())
    logger.info("Sending heartbeat using {}...".format(now))
    neo_driver.exec_cypher(
        "MATCH (n:Monitoring {name: 'heartbeat'}) SET n.value = {timestamp}",
        {"timestamp": now},
    )
    logger.debug("Heartbeat emitted")
    return now


def validate_and_reformat_messages(team, records, validation_logger=logger):
    """This function converts a list of message which has been sent in a
    Kafka topic by some producers. It also prefixes the labels by the
    team's name. Each message has the following format:

        {
          "source": {
            "label": "A",
            "name": "foo",
            "props": {
              "from": 1515241242,
              "to": 1515244850
            }
          },
          "target": {
            "label": "B",
            "name": "bar",
            "props": {
              "from": 1533636245,
              "to": 1533643445
            }
          },
          "rel": {
            "from": 1527847440
            "to": 1527854640
          }
        }

    Sometimes it happens that a producer can not push messages in nested format
    (for performances for example). So we also accept the following format :

        {
          "source_label": "A",
          "source_name": "foo",
          "source_from": 1515241242,
          "source_to": 1515244850,
          "target_label": "B",
          "target_name": "bar",
          "target_from": 1533636245,
          "target_to": 1533643445,
          "rel_from": 1527847440,
          "rel_to": 1527854640
        }

    Note: Every 'props' keys are optionals. The minimal payload is used to create
    a single node without relationship, in this case we just need a name and
    a label of a source and all the other keys can be omitted.

    So this function loops on every message and returns a dict containing the 'nodes'
    and 'rels' keys, themselves containing labels as sub-keys. The consumer loops on
    each key to create nodes in a first time, and then to create relationships in batch
    mode. The returns has the following form :

        {
          "nodes": {
            "Team.A": [{"name": "foo", "props": {"from": 1515241242, "to": 1515244850}}],
            "Team.B": [{"name": "bar", "props": {"from": 1533636245, "to": 1533643445}}]
          },
          "rels": {
            "Team.A": {
              "Team.B": [{"source": "foo", "target": "bar", "props": {"to": 1527847440, "from": 1527854640}}]
            }
          }
        }

    This previous dict will produce 3 Neo4j queries : 1 for the A nodes, 1 for the B nodes and
    1 for the relationship between A and B. In this way we can generate a Cypher with fixed labels
    and pass it to the list of items, resulting from micro-batching.
    """
    data = {"nodes": OrderedDict(), "rels": OrderedDict()}

    def _add_node(node):
        label = "{}_{}".format(team, node["label"])
        if label not in data["nodes"]:
            data["nodes"][label] = []
        data["nodes"][label].append(
            {"name": node["name"], "props": node["props"] if "props" in node else {}}
        )

    def _add_rel(source, target, rel):
        source_label = "{}_{}".format(team, source["label"])
        if source_label not in data["rels"]:
            data["rels"][source_label] = {}

        target_label = "{}_{}".format(team, target["label"])
        if target_label not in data["rels"][source_label]:
            data["rels"][source_label][target_label] = []

        props = {"from": rel.get("from"), "to": rel.get("to")}

        if rel.get("from") is None and rel.get("to") is None:
            props = {"from": int(time.time())}

        data["rels"][source_label][target_label].append(
            {"source": source["name"], "target": target["name"], "props": props}
        )

    for msg in records:
        # Happens when the message is not properly deserialized
        if msg is None:
            validation_logger.warning("[validation] message is not valid JSON, skipped")
            continue

        # Message sent using the EventBus SDK
        if "metadata" in msg:
            msg = msg["metadata"]

        # Handle two different types of messages
        validate = validate_nested_message if "source" in msg else validate_flat_message

        try:
            validate(msg)
        except fastjsonschema.JsonSchemaException as e:
            validation_logger.warning(
                "[validation] message: {} failed validation with error: {}".format(
                    msg, e.message
                )
            )
            continue

        # Handle flat messages and convert it to the nested form
        if "source" not in msg:
            # Convert the source
            m = {
                "source": {
                    "label": msg["source_label"],
                    "name": msg["source_name"],
                    "props": {},
                }
            }
            if "source_from" in msg:
                m["source"]["props"]["from"] = msg["source_from"]
            if "source_to" in msg:
                m["source"]["props"]["to"] = msg["source_to"]

            # Convert the target
            if "target_label" in msg:
                m.update(
                    {
                        "target": {
                            "label": msg["target_label"],
                            "name": msg["target_name"],
                            "props": {},
                        },
                        "rel": {},
                    }
                )
                if "target_from" in msg:
                    m["target"]["props"]["from"] = msg["target_from"]
                if "target_to" in msg:
                    m["target"]["props"]["to"] = msg["target_to"]

                # Convert the rel
                if "rel_from" in msg:
                    m["rel"]["from"] = msg["rel_from"]
                if "rel_to" in msg:
                    m["rel"]["to"] = msg["rel_to"]

            # Replace the original message
            msg = m

        # Process message
        _add_node(node=msg["source"])
        if "target" in msg:
            _add_node(node=msg["target"])
            _add_rel(source=msg["source"], target=msg["target"], rel=msg.get("rel", {}))

    return data


def catch_relationship_validation_errors(neo_result):
    stats = {"relationships_created": 0, "properties_set": 0}
    data = []

    for r in neo_result:
        success = []
        for key in ["R1", "R2", "R3", "R4", "R5", "R6"]:
            # When a predicate match a valid case, one of the result keys (R1, R2,...) contains data
            success.append(bool(r[key]))

        payload = {**r["payload"]}

        # Success if one the list value is True
        if any(success):
            stats["relationships_created"] += 1
            stats["properties_set"] += len(payload.keys())
        else:
            # Key "existing_rel" can be null if it's the first message to create a relationship
            data.append(
                {
                    "payload": payload,
                    "existing_rel": {**r["existing_rel"]} if r["existing_rel"] else {},
                }
            )

    return data, stats


def run_consumer(consumer_config, kafka_config, neo4j_config):
    neo_driver = Neo4jBoltDriver(neo4j_config).connect()

    c = KafkaConsumer(**kafka_config)

    # First we need to retrieve the list of indexes
    records = neo_driver.session.read_transaction(lambda tx: tx.run("CALL db.indexes;"))
    labels = [l[10:-6] for l in records.value()]
    logger.info("[*] Initial indexes : {}".format(labels))

    # Let's start !
    conf = {**kafka_config}
    del conf["sasl_plain_password"]
    topics = consumer_config["kafka"]["topics"]
    logger.info("[*] Starting to consume topic {} : {}".format(topics, conf))

    tps = [TopicPartition(topic, 0) for topic in topics]
    c.assign(tps)
    logger.info("Consumer assigned to: {}".format([tp.topic for tp in tps]))

    last_heartbeat = 0

    while True:

        if int(time.time()) - last_heartbeat >= consumer_config["heartbeat"]["delay"]:
            last_heartbeat = trigger_heartbeat(neo_driver)

        batch_messages = c.poll()

        if batch_messages.values():
            # The consumer currently handle only one partition, so there is no need to iterate
            (topic_partition, records), *_ = batch_messages.items()

            # Keep the first and last offset for debug
            first_offset = records[0].offset
            last_offset = records[-1].offset

            team = topic_partition.topic.split(".")[1]

            # Add extra fields to the logger
            _logger = logger.bind(team=team, batch_id=generate_batch_id())

            # List of formatted messages used in micro-batches
            messages = validate_and_reformat_messages(
                team=team, records=[r.value for r in records], validation_logger=_logger
            )

            # Check if indexes are created
            new_labels = set(messages["nodes"].keys()) - set(labels)
            for lab in new_labels:
                cypher = "CREATE CONSTRAINT ON (l:`$LABEL$`) ASSERT l.name IS UNIQUE;".replace(
                    "$LABEL$", lab
                )
                neo_driver.exec_cypher(cypher, {})
                _logger.info(
                    "[*] {} index created, indexes are now {}".format(lab, labels)
                )
                labels.append(lab)

            start_batch_time = time.time()
            _logger.info(
                "[*] Consuming {} with offsets from #{} to #{}...".format(
                    topic_partition.topic, first_offset, last_offset
                )
            )

            # Let's start the subsets for the nodes
            for label, nodes in messages["nodes"].items():
                cypher = NODE_TEMPLATE.replace("$LABEL$", label)

                start_query_time = time.time()

                _, summary = neo_driver.exec_cypher(cypher, {"nodes": nodes})

                _logger.info(
                    "[nodes] {} done using {} messages in {}s : {}".format(
                        label,
                        len(nodes),
                        round(time.time() - start_query_time, 3),
                        summary.counters,
                    )
                )

            # Let's start the subsets for the relationships
            for source, targets in messages["rels"].items():
                for target, rels in targets.items():
                    cypher = REL_TEMPLATE.replace("$SOURCE$", source)
                    cypher = cypher.replace("$TARGET$", target)

                    start_query_time = time.time()

                    result, summary = neo_driver.exec_cypher(cypher, {"rels": rels})

                    failures, stats = catch_relationship_validation_errors(result)
                    if len(failures):
                        _logger.warning(
                            "[validation] {} relationship(s) failed validation".format(
                                len(failures)
                            )
                        )
                    for f in failures:
                        _logger.warning(
                            "[validation] relationship properties failed validation : {}".format(
                                f
                            )
                        )

                    _logger.info(
                        "[rels] {} -> {} done using {} message(s) in {}s : {}".format(
                            source,
                            target,
                            len(rels),
                            round(time.time() - start_query_time, 3),
                            stats,
                        )
                    )

            _logger.info(
                "[*] Batch done in {} seconds".format(
                    round(time.time() - start_batch_time, 3)
                )
            )

            c.commit()

import json
import os
import ssl
from pathlib import Path

import fastjsonschema
from neo4j.v1 import TRUST_ON_FIRST_USE, basic_auth

from depc import create_app

HOME = os.getenv("DEPC_HOME", str(Path(__file__).resolve().parents[2]))
SCHEMAS_PATH = str(Path(HOME) / "consumer" / "schemas.json")
DEFINITIONS_PATH = str(Path(HOME) / "consumer" / "definitions.json")


app = create_app(environment=os.getenv("DEPC_ENV") or "dev")
CONSUMER_CONFIG = app.config["CONSUMER"]


# Load the JSON schemas to support flat and nested messages
with open(SCHEMAS_PATH, "r") as f_schemas, open(DEFINITIONS_PATH, "r") as f_defs:
    schemas = json.load(f_schemas)
    definitions = json.load(f_defs)

    # Add the definitions in each schema
    schemas["flat"].update(definitions)
    schemas["nested"].update(definitions)

    validate_flat_message = fastjsonschema.compile(schemas["flat"])
    validate_nested_message = fastjsonschema.compile(schemas["nested"])


# Kafka configuration
KAFKA_CONFIG = {
    "bootstrap_servers": CONSUMER_CONFIG["kafka"]["hosts"],
    "security_protocol": "SASL_SSL",
    "sasl_mechanism": "PLAIN",
    "sasl_plain_username": CONSUMER_CONFIG["kafka"]["username"],
    "sasl_plain_password": CONSUMER_CONFIG["kafka"]["password"],
    "ssl_context": ssl.SSLContext(ssl.PROTOCOL_SSLv23),
    "ssl_check_hostname": False,
    "client_id": CONSUMER_CONFIG["kafka"]["client_id"],
    "group_id": CONSUMER_CONFIG["kafka"]["group_id"],
    "value_deserializer": lambda m: json.loads(m.decode("utf-8")),
    "max_poll_records": CONSUMER_CONFIG["kafka"]["batch_size"],
    "auto_offset_reset": "earliest",
    "enable_auto_commit": False,
}


# Graph database configuration
NEO4J_CONFIG = {
    "uri": app.config["NEO4J"]["uri"],
    "auth": basic_auth(
        app.config["NEO4J"]["username"], app.config["NEO4J"]["password"]
    ),
    "encrypted": False,
    "trust": TRUST_ON_FIRST_USE,
}


# Cypher used to create a node
NODE_TEMPLATE = """
UNWIND {nodes} AS rows
MERGE (n:`$LABEL$` {name: rows['name']})
SET n += rows['props']
RETURN n
"""


# Cypher used to link 2 existing nodes with coherent from/to
REL_TEMPLATE = """
UNWIND {rels} AS rows

MATCH (source:`$SOURCE$` {name: rows['source']}), (target:`$TARGET$` {name: rows['target']})
OPTIONAL MATCH (source)-[r:DEPENDS_ON]->(target)

// ###
// ### NO LAST STATE
// ###

// We just receive {from: X}
CALL apoc.do.when(
    r IS NULL AND rows['props']['from'] IS NOT NULL AND rows['props']['to'] IS NULL,
    "MERGE (source)-[rel:DEPENDS_ON{periods: periods, last_state: 'from', last_ts: from}]->(target) RETURN source, rel, target",
    '',
    {source:source, target: target, from: rows['props']['from'], periods: [rows['props']['from']]}
) YIELD value AS R1

// We receive {from: X, to: Y} and X < Y
CALL apoc.do.when(
        r IS NULL AND rows['props']['from'] IS NOT NULL AND rows['props']['to'] IS NOT NULL AND rows['props']['from'] < rows['props']['to'],
    "MERGE (source)-[rel:DEPENDS_ON{periods: periods, last_state: 'to', last_ts: to}]->(target) RETURN source, rel, target",
    '',
    {source:source, target: target, periods: [rows['props']['from'], rows['props']['to']]}
) YIELD value AS R2

// ###
// ### LAST STATE IS FROM
// ###

// There is a previous from (LX), we received {to: Y} and LX < Y
CALL apoc.do.when(
        r IS NOT NULL AND rows['props']['from'] IS NULL AND rows['props']['to'] IS NOT NULL AND r.last_state = 'from' AND r.last_ts < rows['props']['to'],
    "SET rel.last_state = 'to', rel.last_ts = to, rel.periods = rel.periods + new_period RETURN source, rel, target",
    '',
    {source: source, target: target, rel: r, to: rows['props']['to'], new_period: [rows['props']['to']]}
) YIELD value AS R3

// There is a previous from (LX), we received {from: X, to: Y} and LX < Y < X
CALL apoc.do.when(
        r IS NOT NULL AND rows['props']['from'] IS NOT NULL AND rows['props']['to'] IS NOT NULL AND r.last_state = 'from' AND r.last_ts < rows['props']['to'] < rows['props']['from'],
    "SET rel.last_ts = from, rel.periods = rel.periods + new_period RETURN source, rel, target",
    '',
    {source: source, target: target, rel: r, from: rows['props']['from'], new_period: [rows['props']['to'], rows['props']['from']]}
) YIELD value AS R4

// ###
// ### LAST STATE IS TO
// ###

// There is a previous to (LY), we received {from: X} and LY < X
CALL apoc.do.when(
        r IS NOT NULL AND rows['props']['to'] IS NULL AND rows['props']['from'] IS NOT NULL AND r.last_state = 'to' AND r.last_ts < rows['props']['from'],
    "SET rel.last_state = 'from', rel.last_ts = from, rel.periods = rel.periods + new_period RETURN source, rel, target",
    '',
    {source: source, target: target, rel: r, from: rows['props']['from'], new_period: [rows['props']['from']]}
) YIELD value AS R5

// There is a previous to (LY), we receive {from: X, to:Y} and LY < X < Y
CALL apoc.do.when(
        r IS NOT NULL AND rows['props']['from'] IS NOT NULL AND rows['props']['to'] IS NOT NULL AND r.last_state = 'to' AND r.last_ts < rows['props']['from'] < rows['props']['to'],
    "SET rel.last_ts = to, rel.periods = rel.periods + new_period RETURN source, rel, target",
    '',
    {source: source, target: target, rel: r, to: rows['props']['to'], new_period: [rows['props']['from'], rows['props']['to']]}
) YIELD value AS R6

// In all cases we return every result, they will be parsed in the consumer
RETURN rows AS payload, r AS existing_rel, R1, R2, R3, R4, R5, R6
"""

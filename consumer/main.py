#!/bin/env python3

import logging
import os
import sys
from pathlib import Path

sys.path.append(os.getenv("DEPC_HOME", str(Path(__file__).resolve().parents[2])))


if __name__ == "__main__":
    from consumer.kafka_consumer.utils import (
        CONSUMER_CONFIG,
        KAFKA_CONFIG,
        NEO4J_CONFIG,
    )
    from consumer.kafka_consumer import run_consumer

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.getLevelName(
            CONSUMER_CONFIG.get("logging", {}).get("level", "INFO")
        ),
    )
    logger = logging.getLogger("depc_consumer")

    run_consumer(CONSUMER_CONFIG, KAFKA_CONFIG, NEO4J_CONFIG)

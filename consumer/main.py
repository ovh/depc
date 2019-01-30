#!/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import sys

CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
PARENT_FOLDER = os.path.dirname(CURRENT_FOLDER)
sys.path.append(PARENT_FOLDER)


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

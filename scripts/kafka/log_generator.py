"""Synthetic log producer for the real-time log analytics pipeline.

Continuously generates fake log events (random operation type + random user
ID) and publishes them as JSON to the Kafka logs topic, once per interval,
forever. Intended for local development/demo use in place of a real log
source, so that src/spark/log_consumer.py and the Kafka Connect ->
Elasticsearch sink have data to process.

Inputs: none required — reads KAFKA_BOOTSTRAP_SERVERS_HOST,
KAFKA_LOGS_TOPIC, LOG_GEN_SEED, LOG_GEN_STATUS_VALUES,
LOG_GEN_USER_ID_MIN/MAX and LOG_GEN_INTERVAL_SECONDS from
configs/pipeline.env (or the environment), falling back to sane local-dev
defaults. Run against a Kafka broker reachable at the configured host
address (default: localhost:29092, the host-exposed listener from
docker-compose.yml).
Outputs: none returned; messages are published to the Kafka logs topic as
a side effect. Runs until interrupted (Ctrl+C) or the process is killed.
"""

import datetime
import json
import random
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from common.env_config import get_int, get_list, get_str, load_env_file  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_env_file(_REPO_ROOT / "configs" / "pipeline.env")

from kafka import KafkaProducer  # noqa: E402

# Seeded once at import time so runs are reproducible by default; override
# via LOG_GEN_SEED in configs/pipeline.env or the environment.
random.seed(get_int("LOG_GEN_SEED", 42))


def generate_log_record(status_values: list[str], user_id_min: int, user_id_max: int) -> dict[str, Any]:
    """Build one synthetic log event.

    Pulled out as a pure function (no I/O) so it's unit-testable in
    isolation — see tests/test_log_generator.py.

    Args:
        status_values: possible operation types to choose from at random.
        user_id_min: inclusive lower bound of the simulated user ID range.
        user_id_max: inclusive upper bound of the simulated user ID range.

    Returns:
        A dict shaped {"timestamp": str, "status": str, "user": str},
        matching the schema src/spark/log_consumer.py expects to parse.
    """
    return {
        "timestamp": str(datetime.datetime.now()),  # current timestamp
        "status": random.choice(status_values),  # simulated operation type
        "user": str(random.randint(user_id_min, user_id_max)),  # simulated user ID
    }


def main() -> None:
    status_values = get_list("LOG_GEN_STATUS_VALUES", ["put", "get", "auth", "rmi"])
    user_id_min = get_int("LOG_GEN_USER_ID_MIN", 1)
    user_id_max = get_int("LOG_GEN_USER_ID_MAX", 100)
    interval_seconds = get_int("LOG_GEN_INTERVAL_SECONDS", 1)
    topic = get_str("KAFKA_LOGS_TOPIC", "logs")

    # Host-exposed PLAINTEXT_HOST listener (see docker-compose.yml) — this
    # script is meant to be run from the developer's machine, not from
    # inside the docker-compose network (contrast with
    # scripts/kafka/create_topic.py, which uses the in-network
    # "kafka:9092" address).
    bootstrap_servers = get_str("KAFKA_BOOTSTRAP_SERVERS_HOST", "localhost:29092")
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    while True:
        log = generate_log_record(status_values, user_id_min, user_id_max)
        producer.send(topic, log)
        # Flush after every message (rather than batching) so each log is
        # published immediately — this trades producer throughput for
        # lower, more predictable per-message latency, which matches the
        # once-per-interval demo cadence here.
        producer.flush()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()

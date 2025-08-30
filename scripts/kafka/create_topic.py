"""One-shot admin script that creates the Kafka topic used by the pipeline.

Run this once (typically from inside the Docker network, e.g. via
`docker exec` into the kafka or kafka-connect container) before starting
the producer (scripts/kafka/log_generator.py) or the Spark consumer
(src/spark/log_consumer.py). It is not part of the runtime data flow.

Inputs: none required — reads KAFKA_BOOTSTRAP_SERVERS_INTERNAL,
KAFKA_LOGS_TOPIC, KAFKA_LOGS_TOPIC_PARTITIONS and
KAFKA_LOGS_TOPIC_REPLICATION_FACTOR from configs/pipeline.env (or the
environment), falling back to sane local-dev defaults if neither is set.
Outputs: creates the configured topic on the target Kafka cluster; prints
success or failure to stdout.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from common.env_config import get_int, get_str, load_env_file  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_env_file(_REPO_ROOT / "configs" / "pipeline.env")

from kafka.admin import KafkaAdminClient, NewTopic  # noqa: E402


def build_topic() -> tuple[str, NewTopic]:
    """Build the (bootstrap_servers, NewTopic) pair from config/env defaults.

    Kept separate from main() so it can be unit tested without a live
    Kafka broker — see tests/test_create_topic.py.

    Returns:
        A tuple of the Kafka bootstrap servers string and the NewTopic spec
        (name, partition count, replication factor) to create.
    """
    # "kafka:9092" is the broker's address on the docker-compose network
    # (log-pipeline-net), not localhost — this script is meant to run
    # inside that network. Contrast with scripts/kafka/log_generator.py,
    # which uses the host-exposed "localhost:29092" listener because it's
    # typically run from the developer's machine.
    bootstrap_servers = get_str("KAFKA_BOOTSTRAP_SERVERS_INTERNAL", "kafka:9092")
    topic_name = get_str("KAFKA_LOGS_TOPIC", "logs")
    # Single partition / replication factor of 1 is only safe for this
    # local, single-broker dev cluster (see docker-compose.yml,
    # KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1) and would need to change
    # for any multi-broker or production deployment.
    partitions = get_int("KAFKA_LOGS_TOPIC_PARTITIONS", 1)
    replication_factor = get_int("KAFKA_LOGS_TOPIC_REPLICATION_FACTOR", 1)
    topic = NewTopic(name=topic_name, num_partitions=partitions, replication_factor=replication_factor)
    return bootstrap_servers, topic


def main() -> None:
    bootstrap_servers, topic = build_topic()
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers)
    try:
        admin_client.create_topics(new_topics=[topic], validate_only=False)
        print(f"✅ Topic '{topic.name}' created.")
    except Exception as e:
        # Broad except is intentional here: the Kafka admin client raises
        # TopicAlreadyExistsError (among others) and this script is meant
        # to be safely re-runnable, so any failure is treated as
        # non-fatal and logged.
        print(f"⚠️ Topic creation failed (maybe it already exists): {e}")


if __name__ == "__main__":
    main()

"""Tests for scripts/kafka/create_topic.py's topic-spec construction.

Exercises build_topic() directly rather than main(), since main() opens a
real connection to a Kafka admin API — the goal here is to cover the
config-to-topic-spec mapping without needing a live broker.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "kafka"))
from create_topic import build_topic  # noqa: E402


def test_build_topic_uses_defaults(monkeypatch):
    for key in (
        "KAFKA_BOOTSTRAP_SERVERS_INTERNAL",
        "KAFKA_LOGS_TOPIC",
        "KAFKA_LOGS_TOPIC_PARTITIONS",
        "KAFKA_LOGS_TOPIC_REPLICATION_FACTOR",
    ):
        monkeypatch.delenv(key, raising=False)

    bootstrap_servers, topic = build_topic()

    assert bootstrap_servers == "kafka:9092"
    assert topic.name == "logs"
    assert topic.num_partitions == 1
    assert topic.replication_factor == 1


def test_build_topic_respects_env_overrides(monkeypatch):
    monkeypatch.setenv("KAFKA_LOGS_TOPIC", "custom-logs")
    monkeypatch.setenv("KAFKA_LOGS_TOPIC_PARTITIONS", "3")
    monkeypatch.setenv("KAFKA_LOGS_TOPIC_REPLICATION_FACTOR", "2")

    _, topic = build_topic()

    assert topic.name == "custom-logs"
    assert topic.num_partitions == 3
    assert topic.replication_factor == 2

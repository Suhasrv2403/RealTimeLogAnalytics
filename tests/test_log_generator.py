"""Tests for scripts/kafka/log_generator.py's pure log-record generation.

These exercise generate_log_record() directly rather than main(), since
main() opens a real network connection to Kafka — the goal here is to
cover the core mechanics (record shape, bounds, reproducibility) without
needing a live broker.
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "kafka"))
from log_generator import generate_log_record  # noqa: E402


def test_generate_log_record_has_expected_shape():
    record = generate_log_record(["put", "get"], 1, 5)

    assert set(record.keys()) == {"timestamp", "status", "user"}
    assert isinstance(record["timestamp"], str)
    assert isinstance(record["status"], str)
    assert isinstance(record["user"], str)


def test_generate_log_record_status_comes_from_provided_values():
    record = generate_log_record(["only-status"], 1, 1)
    assert record["status"] == "only-status"


def test_generate_log_record_user_id_respects_bounds():
    random.seed(0)
    for _ in range(50):
        record = generate_log_record(["put"], 10, 10)
        assert record["user"] == "10"


def test_generate_log_record_is_reproducible_with_same_seed():
    random.seed(123)
    first = generate_log_record(["put", "get", "auth", "rmi"], 1, 100)
    random.seed(123)
    second = generate_log_record(["put", "get", "auth", "rmi"], 1, 100)

    assert first["status"] == second["status"]
    assert first["user"] == second["user"]


def test_generate_log_record_matches_consumer_schema():
    # src/spark/log_consumer.py parses exactly these three string fields —
    # this test is the producer/consumer contract check called out in the
    # project's review notes (docs/DETAILS.md).
    expected_fields = {"timestamp", "status", "user"}
    record = generate_log_record(["put", "get", "auth", "rmi"], 1, 100)
    assert set(record.keys()) == expected_fields
    assert all(isinstance(v, str) for v in record.values())

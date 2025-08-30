"""Tests for src/common/env_config.py's .env-style loader and typed getters."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from common.env_config import get_int, get_list, get_str, load_env_file  # noqa: E402


def test_load_env_file_sets_unset_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("TEST_KEY_ONE", raising=False)
    monkeypatch.delenv("TEST_KEY_TWO", raising=False)
    env_file = tmp_path / "test.env"
    env_file.write_text("# a comment\nTEST_KEY_ONE=hello\n\nTEST_KEY_TWO=world\n")

    load_env_file(env_file)

    assert os.environ["TEST_KEY_ONE"] == "hello"
    assert os.environ["TEST_KEY_TWO"] == "world"


def test_load_env_file_does_not_override_existing_env(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_KEY_THREE", "already-set")
    env_file = tmp_path / "test.env"
    env_file.write_text("TEST_KEY_THREE=from-file\n")

    load_env_file(env_file)

    assert os.environ["TEST_KEY_THREE"] == "already-set"


def test_load_env_file_missing_file_is_noop(tmp_path):
    load_env_file(tmp_path / "does_not_exist.env")  # should not raise


def test_get_str_default(monkeypatch):
    monkeypatch.delenv("TEST_MISSING_STR", raising=False)
    assert get_str("TEST_MISSING_STR", "fallback") == "fallback"


def test_get_int_default(monkeypatch):
    monkeypatch.delenv("TEST_MISSING_INT", raising=False)
    assert get_int("TEST_MISSING_INT", 7) == 7


def test_get_int_parses_env_value(monkeypatch):
    monkeypatch.setenv("TEST_INT", "13")
    assert get_int("TEST_INT", 0) == 13


def test_get_list_parses_csv_and_trims_whitespace(monkeypatch):
    monkeypatch.setenv("TEST_CSV", "a, b ,c")
    assert get_list("TEST_CSV", []) == ["a", "b", "c"]


def test_get_list_default_when_unset(monkeypatch):
    monkeypatch.delenv("TEST_MISSING_CSV", raising=False)
    assert get_list("TEST_MISSING_CSV", ["x", "y"]) == ["x", "y"]

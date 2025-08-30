"""Tiny dependency-free .env-style config loader shared across the pipeline.

Reads KEY=VALUE pairs from configs/pipeline.env into os.environ without
overriding any variable already set in the real environment (setdefault
semantics), so `KAFKA_LOGS_TOPIC=foo python scripts/kafka/log_generator.py`
still takes precedence over the file. Every caller falls back to its own
hardcoded default if a key is present in neither the environment nor the
config file, so nothing here is required for a script to run — this exists
purely to make hardcoded values overridable from one place instead of
several.
"""

import os
from pathlib import Path


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines from `path` into os.environ.

    No-ops silently if `path` doesn't exist. Blank lines and lines starting
    with '#' are skipped. Existing environment variables are never
    overwritten.

    Args:
        path: location of the .env-style file to load.
    """
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def get_str(key: str, default: str) -> str:
    """Read a string setting from the environment, or `default` if unset."""
    return os.environ.get(key, default)


def get_int(key: str, default: int) -> int:
    """Read an int setting from the environment, or `default` if unset."""
    return int(os.environ.get(key, default))


def get_list(key: str, default: list[str]) -> list[str]:
    """Read a comma-separated list setting, or `default` if unset."""
    raw = os.environ.get(key)
    if raw is None:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]

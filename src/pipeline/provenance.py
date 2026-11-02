"""Where a dataset comes from: the code, the config, the public sources and the
run parameters.

`setup` and `simulate` record them in the OLTP table `run_metadata` (one JSON
value per key); `etl` carries the table to DuckDB; `export` writes it, with the
row counts, as `dataset_metadata.json`.
"""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import psycopg

from src.utils.read_yamls import CONFIG_DIR

ROOT = CONFIG_DIR.parent
RAW_DIR = ROOT / "data" / "raw"


def _digest(paths: list[Path]) -> str:
    sha = hashlib.sha256()
    for path in paths:
        sha.update(path.name.encode())
        sha.update(path.read_bytes())
    return sha.hexdigest()[:16]


def code_version() -> str:
    """The commit, with `-dirty` when tracked files changed; `unknown` without git."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=ROOT, check=False)
    except OSError, subprocess.CalledProcessError:
        return "unknown"
    return commit + ("-dirty" if dirty.returncode else "")


def config_hash() -> str:
    """Hash of every `config/*.yaml`."""
    return _digest(sorted(CONFIG_DIR.glob("*.yaml")))


def source_hashes() -> dict[str, str]:
    """Hash of each public source file in `data/raw`."""
    return {path.name: _digest([path]) for path in sorted(RAW_DIR.glob("*.parquet"))}


def record(conn: psycopg.Connection, **values: Any) -> None:
    """Upsert `values` into `run_metadata`. Doesn't commit."""
    for key, value in values.items():
        conn.execute(
            "INSERT INTO run_metadata (key, value) VALUES (%s, %s) "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (key, json.dumps(value, default=str)),
        )


def read(rows: list[tuple[str, str]]) -> dict[str, Any]:
    """`run_metadata` rows as a dict."""
    return {key: json.loads(value) for key, value in sorted(rows)}

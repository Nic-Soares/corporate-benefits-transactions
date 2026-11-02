"""The YAML config, read once per file.

The folder is `config/`, or another one given with `python -m src.main
--config DIR` (the `BENEFITS_CONFIG_DIR` environment variable), so a run can
use a variant of the rules. Modules read it when imported.
"""

import os
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = Path(os.environ.get("BENEFITS_CONFIG_DIR") or ROOT / "config").resolve()


@cache
def _read(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml(yaml_path: str | Path) -> dict[str, Any]:
    """A YAML file as a dict (a copy: the caller may change it)."""
    return deepcopy(_read(Path(yaml_path).resolve()))


def load_reference(yaml_path: str | Path | None = None) -> dict[str, Any]:
    """Wallets, programs, networks, acquirers, acceptance rules, codes, statuses."""
    return load_yaml(yaml_path or CONFIG_DIR / "reference.yaml")


def load_authorization(yaml_path: str | Path | None = None) -> dict[str, Any]:
    """The issuer's checks, their order and response codes."""
    return load_yaml(yaml_path or CONFIG_DIR / "authorization.yaml")


def load_simulation(yaml_path: str | Path | None = None) -> dict[str, Any]:
    """Volumes, behaviour, calendar, fraud and the expected profile."""
    return load_yaml(yaml_path or CONFIG_DIR / "simulation.yaml")


def load_database(yaml_path: str | Path | None = None) -> dict[str, Any]:
    return load_yaml(yaml_path or CONFIG_DIR / "database.yaml")

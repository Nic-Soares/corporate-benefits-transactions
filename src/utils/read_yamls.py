from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def load_yaml(yaml_path: str | Path) -> dict[str, Any]:
    """Load a YAML file and return the dict."""
    with Path(yaml_path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_business_rules(
    yaml_path: str | Path = CONFIG_DIR / "business_rules.yaml",
) -> dict[str, Any]:
    """Convenience loader for the main business rules file"""
    return load_yaml(yaml_path)


def load_pre_populated_data(
    yaml_path: str | Path = CONFIG_DIR / "pre_populated_data.yaml",
) -> dict[str, Any]:
    return load_yaml(yaml_path)


def load_validation_rules(
    yaml_path: str | Path = CONFIG_DIR / "validation_rules.yaml",
) -> dict[str, Any]:
    return load_yaml(yaml_path)


def load_database(yaml_path: str | Path = CONFIG_DIR / "database.yaml") -> dict[str, Any]:
    return load_yaml(yaml_path)


def load_simulation_config(
    yaml_path: str | Path = CONFIG_DIR / "simulation_config.yaml",
) -> dict[str, Any]:
    return load_yaml(yaml_path)

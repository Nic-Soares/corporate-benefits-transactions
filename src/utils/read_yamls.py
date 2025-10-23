from pathlib import Path
from polars import Unknown
from typing_extensions import Dict
import yaml

def load_yaml(yaml_path: str) -> Dict[str, Unknown]:
    """Load a YAML file and return the dict."""
    p = Path(yaml_path)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_business_rules(yaml_path: str = "config/business_rules.yaml") -> Dict[str, Unknown]:
    """Convenience loader for the main business rules file"""
    return load_yaml(yaml_path)

def load_pre_populated_data(yaml_path: str = "config/pre_populated_data.yaml") -> Dict[str, Unknown]:
  return load_yaml(yaml_path)

def load_validation_rules(yaml_path: str = "config/validation_rules.yaml") -> Dict[str, Unknown]:
  return load_yaml(yaml_path)

def load_database(yaml_path: str = "config/database.yaml") -> Dict[str, Unknown]:
  return load_yaml(yaml_path)

"""Every module in src/ imports."""

import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src"

MODULES = sorted(
    ".".join(p.relative_to(SRC.parent).with_suffix("").parts).removesuffix(".__init__")
    for p in SRC.rglob("*.py")
)


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    importlib.import_module(module)


def test_every_package_has_an_init():
    """No namespace packages: each folder of src/ is a package with an __init__.py."""
    folders = [p for p in SRC.rglob("*") if p.is_dir() and p.name != "__pycache__"]
    assert all((folder / "__init__.py").exists() for folder in folders)

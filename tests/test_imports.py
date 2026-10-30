"""Every module in src/ imports.

Known-broken modules are expected failures until EP-03 fixes them.
"""

import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src"

# Remove each entry as EP-03 fixes it: strict xfail fails the run while a fixed module is listed.
KNOWN_BROKEN: dict[str, str] = {}

MODULES = sorted(
    ".".join(p.relative_to(SRC.parent).with_suffix("").parts).removesuffix(".__init__")
    for p in SRC.rglob("*.py")
    if "notebooks" not in p.parts
)


@pytest.mark.parametrize(
    "module",
    [
        pytest.param(m, marks=pytest.mark.xfail(reason=KNOWN_BROKEN[m], strict=True))
        if m in KNOWN_BROKEN
        else m
        for m in MODULES
    ],
)
def test_module_imports(module):
    importlib.import_module(module)

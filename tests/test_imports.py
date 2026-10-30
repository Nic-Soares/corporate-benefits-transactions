"""Every module in src/ imports.

Known-broken modules are expected failures until EP-03 fixes them.
"""

import importlib
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src"

# Remove each entry as EP-03 fixes it: strict xfail fails the run while a fixed module is listed.
KNOWN_BROKEN = {
    "src.data_generators.reference_data.mcc_and_cnae_loader": "ST-03.4: imports mastercard_mcc_api",
    "src.infrastructure.schema.schema_creator": "ST-03.4: imports src.common",
    "src.processors.load_and_save_reference_data": "ST-03.4: imports mcc_and_cnae_loader",
    "src.validators.balance_and_limits_validations": "ST-03.1: loose module-level code",
    "src.validators.business_rules_validators": "ST-03.1: loose module-level code",
    "src.validators.infrastructure_validations": "ST-03.1: loose module-level code",
}

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

"""Reference-data loaders read config/pre_populated_data.yaml into DataFrames."""

import pytest

from src.data_generators.reference_data.acquirer_loader import load_acquirers
from src.data_generators.reference_data.capture_technologies_loader import (
    load_capture_technologies,
)
from src.data_generators.reference_data.modalities_loader import load_transaction_modalities
from src.data_generators.reference_data.product_loader import load_products
from src.data_generators.reference_data.response_codes_loader import load_response_codes
from src.data_generators.reference_data.segment_loader import load_segments
from src.utils.read_yamls import load_pre_populated_data

DATA = load_pre_populated_data()


@pytest.mark.parametrize(
    ("loader", "key", "columns"),
    [
        (load_products, "products", ["id", "name", "category", "active"]),
        (load_acquirers, "acquirers", ["id", "name", "active"]),
        (load_capture_technologies, "transaction_technologies", ["id", "name", "category"]),
        (load_transaction_modalities, "transaction_modalities", ["id", "name", "type", "active"]),
        (load_response_codes, "response_codes", ["id", "description"]),
        (load_segments, "segments", ["id", "name", "category", "active"]),
    ],
)
def test_loader(loader, key, columns):
    df = loader(DATA)

    assert df.columns == columns
    assert len(df) == len(DATA[key])
    assert df["id"].n_unique() == len(df)
    if "active" in columns:
        assert df["active"].all()

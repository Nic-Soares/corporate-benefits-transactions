"""Where a dataset comes from."""

from src.pipeline import provenance


def test_hashes_are_stable():
    assert provenance.config_hash() == provenance.config_hash()
    assert len(provenance.config_hash()) == 16
    sources = provenance.source_hashes()
    assert {"ibge_municipios.parquet", "mcc_codes.parquet"} <= set(sources)


def test_code_version():
    version = provenance.code_version()
    assert version == "unknown" or len(version.removesuffix("-dirty")) >= 7


def test_read_decodes_json():
    assert provenance.read([("seed", "42"), ("sources", '{"a": "1"}')]) == {
        "seed": 42,
        "sources": {"a": "1"},
    }

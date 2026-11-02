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


def test_another_config_folder(tmp_path):
    """BENEFITS_CONFIG_DIR (`--config`) picks the folder every module reads."""
    import os
    import shutil
    import subprocess
    import sys

    from src.config import CONFIG_DIR

    shutil.copytree(CONFIG_DIR, tmp_path / "cfg")
    code = (
        "from src.config import CONFIG_DIR, load_simulation_config;"
        "print(CONFIG_DIR, load_simulation_config()['data_volumes']['companies'])"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        env=os.environ | {"BENEFITS_CONFIG_DIR": str(tmp_path / "cfg")},
        cwd=CONFIG_DIR.parent,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert out[0] == str((tmp_path / "cfg").resolve()) and out[1].isdigit()

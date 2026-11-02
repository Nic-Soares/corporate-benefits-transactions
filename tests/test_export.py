"""The export: dictionary coverage, quality checks, Parquet files."""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb
import polars as pl
import pytest

from src.data_generators.providers import fake
from src.pipeline import export
from src.pipeline.etl import OLAP_DIR, OLAP_TABLES, build_olap
from src.pipeline.reference import build_reference_tables
from src.simulation.fraud import FraudGenerator
from src.simulation.simulator import TransactionSimulator

TODAY = date(2026, 10, 30)
DOCS_DICTIONARY = Path(__file__).parent.parent / "docs" / "data-dictionary.md"


def olap_columns() -> dict[str, list[str]]:
    duck = duckdb.connect()
    for name in ("01_dimensions.sql", "02_facts.sql"):
        duck.execute((OLAP_DIR / name).read_text())
    columns: dict[str, list[str]] = {}
    for table, column in duck.sql(
        "SELECT table_name, column_name FROM information_schema.columns "
        "ORDER BY table_name, ordinal_position"
    ).fetchall():
        columns.setdefault(table, []).append(column)
    return columns


def test_dictionary_covers_every_column():
    dictionary = export.load_dictionary()
    assert set(dictionary) == set(OLAP_TABLES)
    for table, columns in olap_columns().items():
        assert list(dictionary[table]["columns"]) == columns, table
        assert dictionary[table]["description"]


def test_docs_dictionary_is_current():
    """docs/data-dictionary.md is the rendered dictionary.yaml; regenerate it with
    `uv run python -c "from src.pipeline.export import render_dictionary;
    open('docs/data-dictionary.md', 'w').write(render_dictionary())"`."""
    assert DOCS_DICTIONARY.read_text() == export.render_dictionary()


@pytest.fixture(scope="module")
def olap_file(build_tables, sources, transaction_generator, tmp_path_factory):
    """A simulated OLAP database on disk, with fraud."""
    fake.seed(8, today=TODAY)
    oltp = build_tables() | build_reference_tables(sources.cnae, sources.mcc)
    generator = transaction_generator(oltp, days_back=45)
    n = round(generator.expected_attempts())
    attempts = [generator.generate() for _ in range(n)]
    attempts += FraudGenerator(generator).generate(round(n * 0.01))
    end = datetime(2026, 10, 30)
    result = TransactionSimulator(oltp).run(attempts, end - timedelta(days=45), end)
    oltp |= {
        "transactions": result.transactions,
        "balance_history": result.balance_history,
        "card_wallets": result.card_wallets,
    }
    path = tmp_path_factory.mktemp("olap") / "olap.duckdb"
    with duckdb.connect(str(path)) as duck:
        build_olap(duck, oltp)
    return path


@pytest.fixture
def lenient(monkeypatch):
    """The rate checks are about the full dataset; a small test world only has to be sane."""
    monkeypatch.setattr(export, "APPROVAL_TOLERANCE", 0.3)
    monkeypatch.setattr(export, "FRAUD_SHARE", (0.0001, 0.1))


def test_checks_pass_on_simulated_data(olap_file, lenient):
    with duckdb.connect(str(olap_file), read_only=True) as duck:
        checks = export.quality_checks(duck)
    failed = [(c.name, c.violations, c.detail) for c in checks if not c.passed]
    assert failed == []
    assert len(checks) > 40


def test_export_writes_every_table(olap_file, lenient, tmp_path):
    checks, counts = export.run_export(olap_file, tmp_path)

    for table in OLAP_TABLES:
        assert pl.read_parquet(tmp_path / f"{table}.parquet").height == counts[table]
    assert "fact_transactions" in (tmp_path / "data_dictionary.md").read_text()
    report = (tmp_path / "quality_report.md").read_text()
    assert "❌" not in report and len(checks) == report.count("✅")
    metadata = json.loads((tmp_path / "dataset_metadata.json").read_text())
    assert metadata["rows"] == counts and metadata["synthetic"]
    assert metadata["quality_checks_passed"] == len(checks)


def test_a_broken_dataset_is_not_exported(olap_file, lenient, tmp_path):
    broken = tmp_path / "broken.duckdb"
    broken.write_bytes(olap_file.read_bytes())
    with duckdb.connect(str(broken)) as duck:
        duck.execute(
            "UPDATE fact_balance_movements SET posterior_balance = -1 "
            "WHERE id = (SELECT min(id) FROM fact_balance_movements)"
        )
    with pytest.raises(export.ExportError, match="no balance goes negative"):
        export.run_export(broken, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_rates_are_checked(olap_file, monkeypatch):
    monkeypatch.setattr(export, "FRAUD_SHARE", (0.5, 0.9))
    with duckdb.connect(str(olap_file), read_only=True) as duck:
        fraud = next(c for c in export.quality_checks(duck) if c.name.startswith("fraud share"))
    assert not fraud.passed

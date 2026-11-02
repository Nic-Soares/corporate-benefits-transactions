"""`export`: quality checks on the OLAP database, then one Parquet file per table.

Writes `data/dataset/`: `<table>.parquet`, `data_dictionary.md` (from
`database/olap/dictionary.yaml`), `fact_transactions_sample.csv` (a few rows
to look at), `quality_report.md` and
`dataset_metadata.json` (how the data was made: `src/pipeline/provenance.py`).
A failed check stops the export.
"""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import yaml

from src.config import load_simulation
from src.pipeline import profile, provenance
from src.pipeline.etl import OLAP_DIR, OLAP_FILE, OLAP_TABLES, ROOT

log = logging.getLogger(__name__)

EXPORT_DIR = ROOT / "data" / "dataset"
# A few rows of the transactions as CSV, for a look without loading the whole fact
SAMPLE_ROWS = 10_000
SAMPLE_FILE = "fact_transactions_sample.csv"
DICTIONARY_FILE = OLAP_DIR / "dictionary.yaml"
APPROVAL_TOLERANCE = 0.10
FRAUD_SHARE = (0.001, 0.02)
# The profile's ranges hold on a full dataset; a small test world turns them off
PROFILE_ENFORCED = True
# Never in a public dataset, even hashed or synthetic
FORBIDDEN_COLUMNS = {"cpf", "cpf_hash", "card_number", "card_number_hash", "cnpj"}

# (table, column, referenced table): every non-empty value must exist there
FOREIGN_KEYS = [
    ("fact_transactions", "related_transaction_id", "fact_transactions"),
    ("fact_transactions", "card_id", "dim_cards"),
    ("fact_transactions", "cardholder_id", "dim_cardholders"),
    ("fact_transactions", "company_id", "dim_companies"),
    ("fact_transactions", "program_id", "dim_card_programs"),
    ("fact_transactions", "modality_id", "dim_transaction_modalities"),
    ("fact_transactions", "card_wallet_id", "dim_card_wallets"),
    ("fact_transactions", "wallet_id", "dim_wallets"),
    ("fact_transactions", "establishment_id", "dim_establishments"),
    ("fact_transactions", "terminal_id", "dim_terminals"),
    ("fact_transactions", "acquirer_id", "dim_acquirers"),
    ("fact_transactions", "response_code", "ref_response_codes"),
    ("fact_balance_movements", "card_wallet_id", "dim_card_wallets"),
    ("fact_balance_movements", "card_id", "dim_cards"),
    ("fact_balance_movements", "wallet_id", "dim_wallets"),
    ("fact_balance_movements", "transaction_id", "fact_transactions"),
    ("dim_card_wallets", "card_id", "dim_cards"),
    ("dim_card_wallets", "wallet_id", "dim_wallets"),
    ("dim_cards", "cardholder_id", "dim_cardholders"),
    ("dim_cards", "program_id", "dim_card_programs"),
    ("dim_cards", "modality_id", "dim_transaction_modalities"),
    ("dim_cardholders", "company_id", "dim_companies"),
    ("dim_companies", "parent_id", "dim_companies"),
    ("dim_terminals", "establishment_id", "dim_establishments"),
    ("dim_terminals", "acquirer_id", "dim_acquirers"),
    ("ref_program_wallets", "program_id", "dim_card_programs"),
    ("ref_program_wallets", "wallet_id", "dim_wallets"),
]

# Rules the data must follow: a query counting the rows that break each one
RULES = {
    "cards hold only wallets their program allows": """
        SELECT count(*) FROM dim_card_wallets w JOIN dim_cards c ON c.id = w.card_id
        ANTI JOIN ref_program_wallets p
        ON p.program_id = c.program_id AND p.wallet_id = w.wallet_id""",
    "declines for balance name the wallet": """
        SELECT count(*) FROM fact_transactions
        WHERE decline_reason = 'insufficient_balance' AND card_wallet_id IS NULL""",
    "approved attempts have an authorization code and a wallet": """
        SELECT count(*) FROM fact_transactions WHERE response_code = '00'
        AND (authorization_code IS NULL OR card_wallet_id IS NULL)""",
    "declined attempts have a reason and no authorization": """
        SELECT count(*) FROM fact_transactions WHERE response_code <> '00'
        AND (decline_reason IS NULL OR authorization_code IS NOT NULL)""",
    "only approved transactions are disputed": """
        SELECT count(*) FROM fact_transactions WHERE disputed AND response_code <> '00'""",
    "a fraud scenario exactly when fraud": """
        SELECT count(*) FROM fact_transactions WHERE is_fraud <> (fraud_scenario IS NOT NULL)""",
    "reversals point to an approved purchase": """
        SELECT count(*) FROM fact_transactions r
        LEFT JOIN fact_transactions o ON o.id = r.related_transaction_id
        WHERE r.transaction_type = 'reversal'
        AND (o.id IS NULL OR o.response_code <> '00' OR o.transaction_type <> 'purchase')""",
    "each balance movement starts where the last ended": """
        SELECT count(*) FROM (
          SELECT previous_balance, lag(posterior_balance) OVER (
            PARTITION BY card_wallet_id ORDER BY sequence_number) AS before
          FROM fact_balance_movements)
        WHERE before IS NOT NULL AND before <> previous_balance""",
    "approved attempts only on records active that day": """
        SELECT count(*) FROM fact_transactions f
        JOIN dim_cards c ON c.id = f.card_id
        JOIN dim_cardholders h ON h.id = f.cardholder_id
        JOIN dim_establishments e ON e.id = f.establishment_id
        JOIN dim_terminals t ON t.id = f.terminal_id
        JOIN dim_card_wallets w ON w.id = f.card_wallet_id
        WHERE f.response_code = '00' AND f.transaction_type <> 'reversal' AND (
          (c.status <> 'active' AND f.date::DATE >= c.status_since)
          OR (h.status <> 'active' AND f.date::DATE >= h.status_since)
          OR (e.status <> 'active' AND f.date::DATE >= e.status_since)
          OR (t.status <> 'active' AND f.date::DATE >= t.status_since)
          OR (w.status <> 'active' AND f.date::DATE >= w.status_since))""",
    "no balance goes negative": """
        SELECT count(*) FROM fact_balance_movements WHERE posterior_balance < 0""",
    "the final balance is the last movement": """
        SELECT count(*) FROM dim_card_wallets w
        JOIN (SELECT card_wallet_id, arg_max(posterior_balance, sequence_number) AS last
              FROM fact_balance_movements GROUP BY 1) m ON m.card_wallet_id = w.id
        WHERE w.final_balance <> m.last""",
}


@dataclass
class Check:
    name: str
    violations: int
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.violations == 0


class ExportError(Exception):
    pass


def _count(duck: duckdb.DuckDBPyConnection, query: str) -> int:
    return duck.sql(query).fetchall()[0][0]


def quality_checks(duck: duckdb.DuckDBPyConnection) -> list[Check]:
    checks = []
    columns = duck.sql("SELECT table_name, column_name FROM information_schema.columns").fetchall()
    for table in OLAP_TABLES:
        if (table, "id") in columns:
            duplicates = _count(duck, f"SELECT count(*) - count(DISTINCT id) FROM {table}")
            checks.append(Check(f"{table}.id is unique", duplicates))
    for table, column, referenced in FOREIGN_KEYS:
        key = "mcc_code" if referenced.startswith("ref_mcc") else "id"
        dangling = _count(
            duck,
            f"SELECT count(*) FROM {table} t LEFT JOIN {referenced} r ON r.{key} = t.{column} "
            f"WHERE t.{column} IS NOT NULL AND r.{key} IS NULL",
        )
        checks.append(Check(f"{table}.{column} → {referenced}", dangling))
    for name, query in RULES.items():
        checks.append(Check(name, _count(duck, query)))

    forbidden = sorted({c for _, c in columns} & FORBIDDEN_COLUMNS)
    checks.append(Check("no personal documents", len(forbidden), ", ".join(forbidden)))

    attempts = "FROM fact_transactions WHERE transaction_type <> 'reversal'"
    approval = duck.sql(f"SELECT avg((response_code = '00')::INT) {attempts}").fetchall()[0][0]
    target = load_simulation()["approval_rates"]["overall"]
    off_target = approval is None or abs(approval - target) > APPROVAL_TOLERANCE
    checks.append(
        Check(
            f"approval within {target:.0%} ± {APPROVAL_TOLERANCE:.0%}",
            int(off_target),
            f"{approval:.1%}" if approval is not None else "no attempts",
        )
    )
    fraud = duck.sql(f"SELECT avg(is_fraud::INT) {attempts}").fetchall()[0][0] or 0
    low, high = FRAUD_SHARE
    checks.append(
        Check(f"fraud share in {low:.1%}–{high:.0%}", int(not low <= fraud <= high), f"{fraud:.2%}")
    )
    # The statistical profile: off the expected range, the shape is broken
    if PROFILE_ENFORCED:
        checks += [
            Check(f"profile: {m.name}", int(not m.passed), "" if m.passed else f"{m.value}")
            for m in profile.measures(duck)
        ]
    return checks


def load_dictionary() -> dict:
    return yaml.safe_load(DICTIONARY_FILE.read_text())


def render_dictionary() -> str:
    """The data dictionary as Markdown, with each column's type from the schema."""
    duck = duckdb.connect()
    for name in ("01_dimensions.sql", "02_facts.sql"):
        duck.execute((OLAP_DIR / name).read_text())
    types = {
        (table, column): data_type
        for table, column, data_type in duck.sql(
            "SELECT table_name, column_name, data_type FROM information_schema.columns"
        ).fetchall()
    }
    lines = [
        "# Data dictionary",
        "",
        "Generated from `database/olap/dictionary.yaml` by `python -m src.main export`.",
        "Every record is synthetic.",
    ]
    for table, entry in load_dictionary().items():
        lines += [
            "",
            f"## `{table}`",
            "",
            entry["description"],
            "",
            "| Column | Type | Description |",
            "|---|---|---|",
        ]
        lines += [
            f"| `{column}` | {types[table, column]} | {text} |"
            for column, text in entry["columns"].items()
        ]
    return "\n".join(lines) + "\n"


def render_report(
    checks: list[Check], counts: dict[str, int], measures: list[profile.Measure] = ()
) -> str:
    lines = ["# Quality report", "", "| Check | Result |", "|---|---|"]
    for check in checks:
        result = "✅" if check.passed else f"❌ {check.violations}"
        lines.append(f"| {check.name} | {result} {check.detail}".rstrip() + " |")
    lines += ["", "| Table | Rows |", "|---|---:|"]
    lines += [f"| `{table}` | {rows:,} |" for table, rows in counts.items()]
    lines += profile.render(list(measures)) if measures else []
    return "\n".join(lines) + "\n"


def write_sample(duck: duckdb.DuckDBPyConnection, target: Path) -> None:
    """`SAMPLE_ROWS` transactions drawn at random, the same ones every time, by date."""
    duck.execute(
        f"COPY (SELECT * FROM fact_transactions USING SAMPLE reservoir({SAMPLE_ROWS} ROWS) "
        f"REPEATABLE (42) ORDER BY date, id) TO '{target}' (HEADER, DELIMITER ',')"
    )


def run_export(path: Path = OLAP_FILE, out_dir: Path = EXPORT_DIR) -> tuple[list[Check], dict]:
    """Check the OLAP database at `path` and write the dataset to `out_dir`."""
    if not path.exists():
        raise ExportError(f"No OLAP database at {path}; run etl first")
    with duckdb.connect(str(path), read_only=True) as duck:
        checks = quality_checks(duck)
        failed = [c for c in checks if not c.passed]
        if failed:
            names = "; ".join(f"{c.name} ({c.violations} {c.detail})".strip() for c in failed)
            raise ExportError(f"Quality checks failed: {names}")
        out_dir.mkdir(parents=True, exist_ok=True)
        counts = {}
        for table in OLAP_TABLES:
            target = out_dir / f"{table}.parquet"
            duck.execute(f"COPY {table} TO '{target}' (FORMAT parquet, COMPRESSION zstd)")
            counts[table] = _count(duck, f"SELECT count(*) FROM {table}")
        write_sample(duck, out_dir / SAMPLE_FILE)
        has_run = duck.sql(
            "SELECT count(*) FROM information_schema.tables WHERE table_name = 'run_metadata'"
        ).fetchall()[0][0]
        run = (
            provenance.read(duck.sql("SELECT key, value FROM run_metadata").fetchall())
            if has_run
            else {}
        )
        measures = profile.measures(duck)
    metadata = {
        "generator": "corporate-benefits-transactions",
        "synthetic": True,
        "run": run,
        "export_code_version": provenance.code_version(),
        "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "quality_checks_passed": len(checks),
        "rows": counts,
    }
    (out_dir / "dataset_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (out_dir / "data_dictionary.md").write_text(render_dictionary())
    (out_dir / "quality_report.md").write_text(render_report(checks, counts, measures))
    log.info(
        "Dataset written to %s",
        out_dir.relative_to(ROOT) if out_dir.is_relative_to(ROOT) else out_dir,
    )
    return checks, counts

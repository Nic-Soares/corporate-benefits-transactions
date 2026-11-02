"""The DBML diagrams list the same tables and columns as the SQL schemas."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
TABLE = re.compile(r"^(?:CREATE TABLE IF NOT EXISTS|Table) (\w+) [({]\s*$")
# A column line: a name then a type; constraints and indexes are skipped
COLUMN = re.compile(r"^\s+(\w+)\s+\w")
NOT_COLUMNS = {"FOREIGN", "PRIMARY", "Primary", "UNIQUE", "CHECK", "CONSTRAINT", "indexes", "Note"}


def _tables(path: Path) -> dict[str, list[str]]:
    tables: dict[str, list[str]] = {}
    current = None
    for line in path.read_text().splitlines():
        if match := TABLE.match(line):
            current = tables.setdefault(match[1], [])
        elif line.strip() in {")", ");", "}"}:
            current = None
        elif current is not None and (match := COLUMN.match(line)):
            if match[1] not in NOT_COLUMNS:
                current.append(match[1])
    return tables


@pytest.mark.parametrize(
    ("dbml", "sql"),
    [
        ("database/model/oltp_corporate_benefits.dbml", ["database/oltp_postgres/oltp_schema.sql"]),
        (
            "database/model/olap_corporate_benefits.dbml",
            ["database/olap_duck/01_dimensions.sql", "database/olap_duck/02_facts.sql"],
        ),
    ],
)
def test_dbml_matches_the_sql(dbml, sql):
    expected: dict[str, list[str]] = {}
    for path in sql:
        expected |= _tables(ROOT / path)
    assert expected
    assert _tables(ROOT / dbml) == expected

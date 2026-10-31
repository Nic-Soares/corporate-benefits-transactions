"""`setup` against the real Postgres (`pytest -m db`), in a scratch schema rolled back."""

from datetime import date

import pytest

from src.pipeline.setup import SetupError, run_setup

VOLUMES = {"companies": 6, "cardholder_scale": 0.02, "establishments": 40, "terminals": 50}
TODAY = date(2026, 10, 30)


@pytest.fixture
def conn():
    from src.infrastructure.database.postgres_manager import connect_pg_db

    conn = connect_pg_db()
    conn.execute("CREATE SCHEMA setup_check")
    conn.execute("SET search_path TO setup_check")
    yield conn
    conn.rollback()
    conn.close()


def _fingerprint(conn) -> tuple:
    return conn.execute(
        "SELECT md5(string_agg(id || cnpj, ',' ORDER BY id)) FROM companies"
    ).fetchone()


@pytest.mark.db
def test_setup_fills_the_database(conn, sources):
    counts = run_setup(conn, sources, VOLUMES, seed=1, today=TODAY)

    assert counts["wallets"] == 8
    assert counts["mcc_modalities"] > 700
    assert counts["companies"] == 6
    assert counts["terminals"] == 50
    assert counts["card_wallets"] >= counts["cards"] > 0
    assert counts["transactions"] == 0


@pytest.mark.db
def test_setup_twice(conn, sources):
    run_setup(conn, sources, VOLUMES, seed=1, today=TODAY)
    first = _fingerprint(conn)

    # entities in place: stop, unless asked to replace them
    with pytest.raises(SetupError):
        run_setup(conn, sources, VOLUMES, seed=1, today=TODAY)

    counts = run_setup(conn, sources, VOLUMES, seed=1, today=TODAY, reset=True)
    # the reference upsert didn't duplicate; the same seed gives the same entities
    assert counts["wallets"] == 8
    assert _fingerprint(conn) == first

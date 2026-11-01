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


@pytest.mark.db
def test_simulate_after_setup(conn, sources):
    from src.pipeline.simulate import SimulationError, run_simulation

    run_setup(conn, sources, VOLUMES, seed=1, today=TODAY)
    summary = run_simulation(conn, seed=1, today=TODAY, days=30, per_card_month=4)

    assert summary["transactions"] > 0
    assert 0.5 < summary["approval_rate"] < 1
    stored = conn.execute("SELECT count(*) FROM transactions").fetchone()[0]
    assert stored == summary["transactions"]
    # the balances in card_wallets are the last movements
    mismatched = conn.execute(
        """SELECT count(*) FROM card_wallets c
           JOIN LATERAL (SELECT posterior_balance FROM balance_history b
                         WHERE b.card_wallet_id = c.id
                         ORDER BY operation_date DESC, id DESC LIMIT 1) last ON true
           WHERE c.current_balance <> last.posterior_balance"""
    ).fetchone()[0]
    assert mismatched == 0

    # balances moved: a second run has to start over from setup
    with pytest.raises(SimulationError):
        run_simulation(conn, seed=1, today=TODAY, days=30, per_card_month=4)


@pytest.mark.db
def test_simulate_needs_the_setup_day(conn, sources):
    from src.pipeline.simulate import SimulationError, run_simulation

    run_setup(conn, sources, VOLUMES, seed=1, today=TODAY)
    with pytest.raises(SimulationError, match="before the generated data"):
        run_simulation(conn, seed=1, today=date(2020, 1, 1), days=30, per_card_month=4)

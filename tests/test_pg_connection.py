import pytest

from src.infrastructure.database.postgres_manager import connect_pg_db


@pytest.mark.db
def test_pg_connection():
    """Needs `docker compose up -d` and a filled-in .env."""
    conn = connect_pg_db()
    assert conn, "connect_pg_db() returned no connection"
    try:
        assert conn.execute("SELECT 1").fetchone() == (1,)
    finally:
        conn.close()

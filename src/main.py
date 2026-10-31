"""Command line: `python -m src.main setup [--seed N] [--today YYYY-MM-DD] [--reset]`.

`simulate` arrives with the transaction simulator (EP-08), `export` with the
dataset export (EP-10).
"""

import argparse
import logging
import sys
from datetime import date

from src.infrastructure.database.postgres_manager import connect_pg_db
from src.pipeline.setup import SetupError, run_setup
from src.pipeline.sources import fetch_sources
from src.utils.read_yamls import load_simulation_config

log = logging.getLogger("src.main")


def setup(args: argparse.Namespace) -> int:
    sources = fetch_sources()
    volumes = load_simulation_config()["data_volumes"]
    with connect_pg_db() as conn:
        try:
            counts = run_setup(conn, sources, volumes, args.seed, args.today, args.reset)
        except SetupError as error:
            log.error("%s", error)
            return 1
        conn.commit()
    width = max(map(len, counts))
    for table, rows in counts.items():
        log.info("  %s %s", table.ljust(width), f"{rows:>9,}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.main")
    commands = parser.add_subparsers(dest="command", required=True)

    setup_parser = commands.add_parser(
        "setup", help="create the OLTP schema, load the reference tables and the entities"
    )
    setup_parser.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    setup_parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="reference day for every generated date (default: today)",
    )
    setup_parser.add_argument(
        "--reset", action="store_true", help="replace the entities already in the database"
    )
    setup_parser.set_defaults(run=setup)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())

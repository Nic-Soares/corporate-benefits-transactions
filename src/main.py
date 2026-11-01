"""Command line.

    python -m src.main setup [--seed N] [--today YYYY-MM-DD] [--reset]
    python -m src.main simulate [--seed N] [--today YYYY-MM-DD] [--days N]

`export` arrives with the dataset export (EP-10).
"""

import argparse
import logging
import sys
from datetime import date

from src.infrastructure.database.postgres_manager import connect_pg_db
from src.pipeline.setup import SetupError, run_setup
from src.pipeline.simulate import SimulationError, run_simulation, simulation_defaults
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


def simulate(args: argparse.Namespace) -> int:
    days, per_card_month = simulation_defaults()
    with connect_pg_db() as conn:
        try:
            summary = run_simulation(conn, args.seed, args.today, args.days or days, per_card_month)
        except SimulationError as error:
            log.error("%s", error)
            return 1
        conn.commit()
    log.info("  transactions    %9s", f"{summary['transactions']:,}")
    log.info("  balance_history %9s", f"{summary['balance_history']:,}")
    log.info("  approved        %8.1f%%", 100 * summary["approval_rate"])
    log.info("  fraud           %9s", f"{summary['fraud']:,}")
    log.info("  disputed        %9s", f"{summary['disputed']:,}")
    for code, reason, rows in summary["answers"].head(8).iter_rows():
        log.info("    %s %-30s %7s", code, reason or "approved", f"{rows:,}")
    return 0


def _common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=date.today(),
        help="reference day (default: today); use the same for setup and simulate",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.main")
    commands = parser.add_subparsers(dest="command", required=True)

    setup_parser = commands.add_parser(
        "setup", help="create the OLTP schema, load the reference tables and the entities"
    )
    _common_options(setup_parser)
    setup_parser.add_argument(
        "--reset", action="store_true", help="replace the entities already in the database"
    )
    setup_parser.set_defaults(run=setup)

    simulate_parser = commands.add_parser(
        "simulate", help="answer purchase attempts over the days before --today"
    )
    _common_options(simulate_parser)
    simulate_parser.add_argument(
        "--days", type=int, help="length of the window (default: simulation.days in the config)"
    )
    simulate_parser.set_defaults(run=simulate)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())

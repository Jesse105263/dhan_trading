import argparse
from datetime import date
from pathlib import Path

from app.logging_config import configure_logging
from app.settings import DERIVATIVE_IMPORT_SETTINGS
from services.derivative_security_master import (
    DerivativeSecurityMasterImporter,
    SecurityMasterDownloader,
)


def _parse_aliases(values: list[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(
                f"Invalid alias '{value}'. Use SOURCE=TARGET."
            )
        source, target = value.split("=", maxsplit=1)
        source = source.strip().upper()
        target = target.strip().upper()
        if not source or not target:
            raise ValueError(
                f"Invalid alias '{value}'. Use SOURCE=TARGET."
            )
        aliases[source] = target
    return aliases


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Dhan NSE stock derivative contracts."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", type=Path)
    source.add_argument("--url")
    parser.add_argument("--as-of-date", type=date.fromisoformat)
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    configure_logging()
    aliases = dict(DERIVATIVE_IMPORT_SETTINGS.symbol_aliases)
    aliases.update(_parse_aliases(arguments.alias))

    importer = DerivativeSecurityMasterImporter(
        downloader=SecurityMasterDownloader(
            timeout_seconds=DERIVATIVE_IMPORT_SETTINGS.request_timeout_seconds
        ),
        max_persisted_failures=(
            DERIVATIVE_IMPORT_SETTINGS.max_persisted_failures
        ),
    )

    summary = importer.run(
        source_url=(
            arguments.url
            or (
                None
                if arguments.file is not None
                else DERIVATIVE_IMPORT_SETTINGS.source_url
            )
        ),
        source_file=arguments.file,
        symbol_aliases=aliases,
        as_of_date=arguments.as_of_date,
        dry_run=arguments.dry_run,
    )

    print(f"Import status: {summary.status}")
    print(f"Run ID: {summary.run_id or 'not persisted'}")
    print(f"Rows read: {summary.rows_read}")
    print(f"Eligible rows: {summary.rows_eligible}")
    print(f"Contracts upserted: {summary.contracts_upserted}")
    print(f"Contracts deactivated: {summary.contracts_deactivated}")
    print(f"Rows rejected: {summary.rows_rejected}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import csv
import logging
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable, Mapping
from uuid import UUID, uuid4

import requests

from services.derivative_contract_repository import (
    DerivativeContract,
    DerivativeContractRepository,
)
from services.derivative_import_repository import (
    DerivativeImportFailure,
    DerivativeImportRepository,
)
from services.error_sanitizer import sanitize_error_message
from services.instrument_repository import InstrumentRepository


logger = logging.getLogger(__name__)

_REQUIRED_COLUMNS = {
    "EXCH_ID",
    "SEGMENT",
    "SECURITY_ID",
    "INSTRUMENT",
    "UNDERLYING_SYMBOL",
    "SYMBOL_NAME",
    "LOT_SIZE",
    "SM_EXPIRY_DATE",
    "STRIKE_PRICE",
    "OPTION_TYPE",
    "TICK_SIZE",
}


@dataclass(frozen=True)
class SecurityMasterSource:
    path: Path
    source_url: str | None
    source_timestamp: datetime | None
    temporary: bool = False


@dataclass(frozen=True)
class ParsedSecurityMaster:
    contracts: tuple[DerivativeContract, ...]
    failures: tuple[tuple[int, str | None, str | None, Exception], ...]
    rows_read: int
    rows_eligible: int


@dataclass(frozen=True)
class DerivativeImportSummary:
    run_id: UUID | None
    status: str
    rows_read: int
    rows_eligible: int
    contracts_upserted: int
    contracts_deactivated: int
    rows_rejected: int


class SecurityMasterDownloader:
    def __init__(self, timeout_seconds: int = 60) -> None:
        self.timeout_seconds = timeout_seconds

    def download(self, url: str) -> SecurityMasterSource:
        temporary = tempfile.NamedTemporaryFile(
            prefix="dhan-security-master-",
            suffix=".csv",
            delete=False,
        )
        path = Path(temporary.name)

        try:
            with requests.get(
                url,
                stream=True,
                timeout=self.timeout_seconds,
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        temporary.write(chunk)
                last_modified = response.headers.get("Last-Modified")
        except requests.RequestException as error:
            temporary.close()
            path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Unable to download Dhan security master: {error}"
            ) from error
        finally:
            temporary.close()

        if path.stat().st_size == 0:
            path.unlink(missing_ok=True)
            raise RuntimeError("Downloaded Dhan security master is empty.")

        source_timestamp = None
        if last_modified:
            try:
                source_timestamp = parsedate_to_datetime(last_modified)
                if source_timestamp.tzinfo is not None:
                    source_timestamp = source_timestamp.astimezone(
                        timezone.utc
                    ).replace(tzinfo=None)
            except (TypeError, ValueError, OverflowError):
                source_timestamp = None

        return SecurityMasterSource(
            path=path,
            source_url=url,
            source_timestamp=source_timestamp,
            temporary=True,
        )


class DerivativeSecurityMasterParser:
    def __init__(
        self,
        supported_underlyings: Iterable[str],
        symbol_aliases: Mapping[str, str] | None = None,
        as_of_date: date | None = None,
    ) -> None:
        self.supported_underlyings = {
            self._clean_symbol(symbol)
            for symbol in supported_underlyings
            if self._clean_symbol(symbol)
        }
        self.symbol_aliases = {
            self._clean_symbol(source): self._clean_symbol(target)
            for source, target in (symbol_aliases or {}).items()
        }
        self.as_of_date = as_of_date or date.today()

    def parse(self, path: Path) -> ParsedSecurityMaster:
        contracts: dict[tuple[str, str, str], DerivativeContract] = {}
        failures: list[tuple[int, str | None, str | None, Exception]] = []
        rows_read = 0
        rows_eligible = 0

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = {str(column).strip().upper() for column in reader.fieldnames or []}
            missing = sorted(_REQUIRED_COLUMNS - columns)
            if missing:
                raise RuntimeError(
                    "Security master is missing required columns: "
                    + ", ".join(missing)
                )

            for row_number, row in enumerate(reader, start=2):
                rows_read += 1
                normalized = {
                    str(key).strip().upper(): value
                    for key, value in row.items()
                    if key is not None
                }

                if not self._is_candidate(normalized):
                    continue

                raw_underlying = self._clean_symbol(
                    normalized.get("UNDERLYING_SYMBOL")
                )
                underlying = self.symbol_aliases.get(
                    raw_underlying,
                    raw_underlying,
                )

                if underlying not in self.supported_underlyings:
                    continue

                expiry_text = self._clean_text(
                    normalized.get("SM_EXPIRY_DATE")
                )
                try:
                    parsed_expiry = date.fromisoformat(expiry_text)
                except ValueError:
                    parsed_expiry = None

                if (
                    parsed_expiry is not None
                    and parsed_expiry < self.as_of_date
                ):
                    continue

                rows_eligible += 1
                security_id = self._clean_text(
                    normalized.get("SECURITY_ID")
                )
                trading_symbol = self._clean_text(
                    normalized.get("SYMBOL_NAME")
                )

                try:
                    contract = self._build_contract(
                        normalized,
                        underlying,
                    ).normalized()
                    identity = (
                        contract.exchange,
                        contract.segment,
                        contract.security_id,
                    )
                    if identity in contracts:
                        raise ValueError(
                            "Duplicate derivative contract identity in security master."
                        )
                    contracts[identity] = contract
                except Exception as error:
                    failures.append(
                        (
                            row_number,
                            security_id or None,
                            trading_symbol or None,
                            error,
                        )
                    )

        return ParsedSecurityMaster(
            contracts=tuple(contracts.values()),
            failures=tuple(failures),
            rows_read=rows_read,
            rows_eligible=rows_eligible,
        )

    def _is_candidate(self, row: Mapping[str, object]) -> bool:
        exchange = self._clean_text(row.get("EXCH_ID")).upper()
        segment = self._clean_text(row.get("SEGMENT")).upper()
        instrument = self._clean_text(row.get("INSTRUMENT")).upper()
        return (
            exchange == "NSE"
            and segment == "D"
            and instrument in {"FUTSTK", "OPTSTK"}
        )

    def _build_contract(
        self,
        row: Mapping[str, object],
        underlying: str,
    ) -> DerivativeContract:
        instrument_type = self._clean_text(
            row.get("INSTRUMENT")
        ).upper()
        expiry = date.fromisoformat(
            self._clean_text(row.get("SM_EXPIRY_DATE"))
        )
        if expiry < self.as_of_date:
            raise ValueError("Contract expiry is before the import as-of date.")

        lot_size_decimal = self._decimal(row.get("LOT_SIZE"), "LOT_SIZE")
        if lot_size_decimal != lot_size_decimal.to_integral_value():
            raise ValueError("LOT_SIZE must be a whole number.")

        strike = None
        option_type = None
        if instrument_type == "OPTSTK":
            strike = self._decimal(row.get("STRIKE_PRICE"), "STRIKE_PRICE")
            option_type = self._clean_text(row.get("OPTION_TYPE")).upper()

        return DerivativeContract(
            exchange="NSE",
            segment="NSE_FNO",
            security_id=self._required_text(row.get("SECURITY_ID"), "SECURITY_ID"),
            trading_symbol=self._required_text(row.get("SYMBOL_NAME"), "SYMBOL_NAME"),
            underlying_symbol=underlying,
            instrument_type=instrument_type,
            expiry=expiry,
            strike=strike,
            option_type=option_type,
            lot_size=int(lot_size_decimal),
            tick_size=self._decimal(row.get("TICK_SIZE"), "TICK_SIZE"),
            is_active=True,
        )

    @staticmethod
    def _decimal(value: object, field_name: str) -> Decimal:
        text = DerivativeSecurityMasterParser._required_text(
            value,
            field_name,
        )
        try:
            return Decimal(text)
        except InvalidOperation as error:
            raise ValueError(f"{field_name} must be numeric.") from error

    @staticmethod
    def _required_text(value: object, field_name: str) -> str:
        text = DerivativeSecurityMasterParser._clean_text(value)
        if not text:
            raise ValueError(f"{field_name} is required.")
        return text

    @staticmethod
    def _clean_text(value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _clean_symbol(value: object) -> str:
        symbol = DerivativeSecurityMasterParser._clean_text(value).upper()
        if symbol.endswith("-EQ"):
            symbol = symbol[:-3]
        return symbol


class DerivativeSecurityMasterImporter:
    def __init__(
        self,
        contract_repository: DerivativeContractRepository | None = None,
        import_repository: DerivativeImportRepository | None = None,
        instrument_repository: InstrumentRepository | None = None,
        downloader: SecurityMasterDownloader | None = None,
        max_persisted_failures: int = 1000,
    ) -> None:
        self.contract_repository = contract_repository or DerivativeContractRepository()
        self.import_repository = import_repository or DerivativeImportRepository()
        self.instrument_repository = instrument_repository or InstrumentRepository()
        self.downloader = downloader or SecurityMasterDownloader()
        self.max_persisted_failures = max_persisted_failures

    def run(
        self,
        source_url: str | None = None,
        source_file: Path | None = None,
        symbol_aliases: Mapping[str, str] | None = None,
        as_of_date: date | None = None,
        dry_run: bool = False,
    ) -> DerivativeImportSummary:
        if (source_url is None) == (source_file is None):
            raise ValueError("Provide exactly one of source_url or source_file.")

        source = (
            self.downloader.download(source_url)
            if source_url is not None
            else SecurityMasterSource(
                path=Path(source_file).expanduser().resolve(),
                source_url=None,
                source_timestamp=datetime.fromtimestamp(
                    Path(source_file).expanduser().resolve().stat().st_mtime
                ),
            )
        )

        try:
            supported = {
                instrument.symbol
                for instrument in self.instrument_repository.list_active_quote_instruments()
            }
            if not supported:
                raise RuntimeError("No supported underlying instruments found.")

            parsed = DerivativeSecurityMasterParser(
                supported_underlyings=supported,
                symbol_aliases=symbol_aliases,
                as_of_date=as_of_date,
            ).parse(source.path)

            if not parsed.contracts:
                raise RuntimeError(
                    "Security master produced zero valid derivative contracts."
                )

            if dry_run:
                return DerivativeImportSummary(
                    run_id=None,
                    status="DRY_RUN",
                    rows_read=parsed.rows_read,
                    rows_eligible=parsed.rows_eligible,
                    contracts_upserted=0,
                    contracts_deactivated=0,
                    rows_rejected=len(parsed.failures),
                )

            run_id = uuid4()
            started_at = datetime.now()
            upserted = 0
            deactivated = 0
            self.import_repository.start_run(
                run_id=run_id,
                started_at=started_at,
                source_url=source.source_url,
                source_file_name=source.path.name,
                source_timestamp=source.source_timestamp,
            )

            try:
                failures = [
                    DerivativeImportFailure(
                        run_id=run_id,
                        row_number=row_number,
                        security_id=security_id,
                        trading_symbol=trading_symbol,
                        error_type=type(error).__name__,
                        error_message=sanitize_error_message(str(error)),
                        occurred_at=datetime.now(),
                    )
                    for row_number, security_id, trading_symbol, error
                    in parsed.failures[: self.max_persisted_failures]
                ]
                self.import_repository.insert_failures(failures)

                upserted = self.contract_repository.bulk_upsert(parsed.contracts)
                deactivated = self.contract_repository.deactivate_missing(
                    exchange="NSE",
                    segment="NSE_FNO",
                    active_security_ids=[
                        contract.security_id for contract in parsed.contracts
                    ],
                )

                self.import_repository.complete_run(
                    run_id=run_id,
                    completed_at=datetime.now(),
                    rows_read=parsed.rows_read,
                    rows_eligible=parsed.rows_eligible,
                    contracts_upserted=upserted,
                    contracts_deactivated=deactivated,
                    rows_rejected=len(parsed.failures),
                )
            except Exception as error:
                self.import_repository.fail_run(
                    run_id=run_id,
                    completed_at=datetime.now(),
                    rows_read=parsed.rows_read,
                    rows_eligible=parsed.rows_eligible,
                    contracts_upserted=upserted,
                    contracts_deactivated=deactivated,
                    rows_rejected=len(parsed.failures),
                    error_message=sanitize_error_message(str(error)),
                )
                raise

            return DerivativeImportSummary(
                run_id=run_id,
                status="COMPLETED",
                rows_read=parsed.rows_read,
                rows_eligible=parsed.rows_eligible,
                contracts_upserted=upserted,
                contracts_deactivated=deactivated,
                rows_rejected=len(parsed.failures),
            )
        finally:
            if source.temporary:
                source.path.unlink(missing_ok=True)

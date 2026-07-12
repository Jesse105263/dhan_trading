from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from typing import (
    Iterable,
    Protocol,
    TYPE_CHECKING,
)


if TYPE_CHECKING:
    from services.derivative_contract_repository import (
        DerivativeContract,
    )
    from services.derivative_import_repository import (
        DerivativeImportFailure,
    )
    from services.expiry_repository import (
        ExpiryAvailability,
    )
    from services.failure_repository import (
        PipelineFailure,
    )
    from services.feature_repository import (
        FeatureInput,
        MarketFeature,
    )
    from services.instrument_repository import (
        Instrument,
    )
    from services.snapshot_repository import (
        ScannerSnapshot,
    )
    from services.underlying_quote_repository import (
        UnderlyingQuote,
    )
    from services.metrics_repository import (
    StageMetric,
    )


class InstrumentRepositoryContract(
    Protocol
):
    def list_active_quote_instruments(
        self,
    ) -> list[Instrument]:
        ...

    def count(self) -> int:
        ...

    def bulk_upsert(
        self,
        instruments: Iterable[Instrument],
    ) -> int:
        ...


class UnderlyingQuoteRepositoryContract(
    Protocol
):
    def latest_batch_timestamp(
        self,
    ) -> datetime | None:
        ...

    def list_latest_batch(
        self,
    ) -> list[UnderlyingQuote]:
        ...


class SnapshotRepositoryContract(
    Protocol
):
    def start_run(
        self,
        run_id: str,
        started_at: datetime,
        quote_timestamp: datetime,
        instrument_count: int,
    ) -> None:
        ...

    def complete_run(
        self,
        run_id: str,
        completed_at: datetime,
        snapshot_count: int,
    ) -> None:
        ...

    def bulk_insert(
        self,
        snapshots: Iterable[
            ScannerSnapshot
        ],
    ) -> int:
        ...

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        ...


class FeatureRepositoryContract(
    Protocol
):
    def list_inputs_for_run(
        self,
        run_id: str,
        lookback_runs: int = 20,
    ) -> list[FeatureInput]:
        ...

    def bulk_upsert(
        self,
        features: Iterable[
            MarketFeature
        ],
    ) -> int:
        ...

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        ...

    def complete_run(
        self,
        run_id: str,
        feature_count: int,
        completed_at: datetime,
    ) -> None:
        ...


class PipelineRunRepositoryContract(
    Protocol
):
    def start_run(
        self,
        run_id: str,
        started_at: datetime,
    ) -> None:
        ...

    def complete_run(
        self,
        run_id: str,
        completed_at: datetime,
    ) -> None:
        ...

    def fail_run(
        self,
        run_id: str,
        completed_at: datetime,
    ) -> None:
        ...


class FailureRepositoryContract(
    Protocol
):
    def insert(
        self,
        failure: PipelineFailure,
    ) -> int:
        ...

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        ...
    
class MetricsRepositoryContract(
    Protocol
):
    def insert(
        self,
        metric: StageMetric,
    ) -> int:
        ...

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        ...

class DerivativeContractRepositoryContract(
    Protocol
):
    def bulk_upsert(
        self,
        contracts: Iterable[DerivativeContract],
    ) -> int:
        ...

    def get_by_identity(
        self,
        exchange: str,
        segment: str,
        security_id: str,
    ) -> DerivativeContract | None:
        ...

    def list_active_by_underlying(
        self,
        underlying_symbol: str,
        expiry: date | None = None,
        instrument_type: str | None = None,
    ) -> list[DerivativeContract]:
        ...

    def list_active_expiries(
        self,
        underlying_symbol: str,
        instrument_type: str | None = None,
    ) -> list[date]:
        ...

    def deactivate_missing(
        self,
        exchange: str,
        segment: str,
        active_security_ids: Iterable[str],
    ) -> int:
        ...

    def count(
        self,
        active_only: bool = False,
    ) -> int:
        ...


class ExpiryRepositoryContract(Protocol):
    def list_available(
        self,
        underlying_symbol: str,
        instrument_type: str = "OPTSTK",
        on_or_after: date | None = None,
    ) -> list[ExpiryAvailability]:
        ...

    def is_available(
        self,
        underlying_symbol: str,
        expiry: date,
        instrument_type: str = "OPTSTK",
    ) -> bool:
        ...

    def count_underlyings(
        self,
        instrument_type: str = "OPTSTK",
        on_or_after: date | None = None,
    ) -> int:
        ...


class DerivativeImportRepositoryContract(Protocol):
    def start_run(
        self,
        run_id: UUID,
        started_at: datetime,
        source_url: str | None,
        source_file_name: str | None,
        source_timestamp: datetime | None,
    ) -> None:
        ...

    def insert_failures(
        self,
        failures: Iterable[DerivativeImportFailure],
    ) -> int:
        ...

    def complete_run(
        self,
        run_id: UUID,
        completed_at: datetime,
        rows_read: int,
        rows_eligible: int,
        contracts_upserted: int,
        contracts_deactivated: int,
        rows_rejected: int,
    ) -> None:
        ...

    def fail_run(
        self,
        run_id: UUID,
        completed_at: datetime,
        rows_read: int,
        rows_eligible: int,
        contracts_upserted: int,
        contracts_deactivated: int,
        rows_rejected: int,
        error_message: str,
    ) -> None:
        ...

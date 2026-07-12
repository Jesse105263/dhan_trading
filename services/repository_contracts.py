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
    from services.option_chain_models import (
        OptionQuoteSnapshot,
        UnderlyingIdentity,
    )
    from services.option_analytics_models import (
        CompletedOptionChainRun,
        OptionChainAnalytics,
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


class OptionChainRepositoryContract(Protocol):
    def resolve_underlying(
        self,
        underlying_symbol: str,
    ) -> UnderlyingIdentity:
        ...

    def start_run(
        self,
        run_id: UUID,
        identity: UnderlyingIdentity,
        expiry: date,
        requested_at: datetime,
    ) -> None:
        ...

    def complete_run_with_quotes(
        self,
        run_id: UUID,
        completed_at: datetime,
        spot_price: object | None,
        quotes: Iterable[OptionQuoteSnapshot],
    ) -> int:
        ...

    def fail_run(
        self,
        run_id: UUID,
        completed_at: datetime,
        error_message: str,
    ) -> None:
        ...


class OptionAnalyticsRepositoryContract(Protocol):
    def get_completed_run(
        self,
        run_id: UUID,
    ) -> CompletedOptionChainRun:
        ...

    def upsert(
        self,
        analytics: OptionChainAnalytics,
    ) -> OptionChainAnalytics:
        ...


class OptionAnalyticsHistoryRepositoryContract(Protocol):
    def list_history(
        self,
        underlying_symbol: str,
        expiry: date,
        limit: int = 100,
    ) -> list[OptionChainAnalytics]:
        ...

    def get_consecutive_pair(
        self,
        current_analytics_id: UUID,
    ):
        ...

    def upsert_change(self, change):
        ...

if TYPE_CHECKING:
    from services.option_ranking_models import OptionRankingCandidate, OptionRankingResult


class OptionRankingRepositoryContract(Protocol):
    def list_latest_candidates(self, as_of: datetime) -> list[OptionRankingCandidate]:
        ...

    def persist(self, result: OptionRankingResult) -> OptionRankingResult:
        ...

if TYPE_CHECKING:
    from services.option_contract_selection_models import RankedUnderlying, ContractCandidate, OptionContractSelectionResult

class OptionContractSelectionRepositoryContract(Protocol):
    def list_ranked_underlyings(self, ranking_run_id: UUID, limit: int) -> list[RankedUnderlying]: ...
    def list_contract_candidates(self, ranked: RankedUnderlying) -> list[ContractCandidate]: ...
    def persist(self, result: OptionContractSelectionResult) -> OptionContractSelectionResult: ...

if TYPE_CHECKING:
    from services.option_risk_models import OptionRiskResult, SelectedOptionContract


class OptionRiskRepositoryContract(Protocol):
    def list_selected_contracts(self, selection_run_id: UUID) -> list[SelectedOptionContract]:
        ...

    def persist(self, result: OptionRiskResult) -> OptionRiskResult:
        ...


class OptionSignalRepositoryContract(Protocol):
    def list_approved_candidates(self, risk_run_id: UUID):
        ...

    def persist(self, result):
        ...


class MarketReplayRepositoryContract(Protocol):
    def load_lineage(self, signal_run_id: UUID):
        ...

    def persist(self, result):
        ...


class OptionBacktestRepositoryContract(Protocol):
    def list_signals(self, signal_run_id: UUID):
        ...

    def list_future_marks(self, signal, as_of: datetime):
        ...

    def persist(self, result):
        ...


class ReadApiRepositoryContract(Protocol):
    def list_latest(self, resource: str, limit: int) -> list[dict]:
        ...

    def get_run(self, resource: str, run_id: UUID) -> dict | None:
        ...

    def health(self) -> dict:
        ...

from datetime import datetime
from typing import Any

from services.repository_contracts import (
    SnapshotRepositoryContract,
    UnderlyingQuoteRepositoryContract,
)
from services.snapshot_repository import (
    ScannerSnapshot,
    SnapshotRepository,
)
from services.stage import Stage
from services.underlying_quote_repository import (
    UnderlyingQuoteRepository,
)


class SnapshotStage(Stage):
    def __init__(
        self,
        quote_repository: (
            UnderlyingQuoteRepositoryContract | None
        ) = None,
        snapshot_repository: (
            SnapshotRepositoryContract | None
        ) = None,
    ) -> None:
        super().__init__("Snapshot Engine")

        self.quote_repository = (
            quote_repository
            or UnderlyingQuoteRepository()
        )

        self.snapshot_repository = (
            snapshot_repository
            or SnapshotRepository()
        )

    def run(
        self,
        context: dict[str, Any],
    ) -> None:
        run_id = context.get("run_id")
        started_at = context.get(
            "pipeline_started_at"
        )

        if not run_id:
            raise RuntimeError(
                "Pipeline context is missing run_id."
            )

        if not isinstance(started_at, datetime):
            raise RuntimeError(
                "Pipeline context is missing "
                "pipeline_started_at."
            )

        quotes = (
            self.quote_repository
            .list_latest_batch()
        )

        if not quotes:
            raise RuntimeError(
                "No underlying quote batch is available "
                "for snapshot creation."
            )

        quote_timestamps = {
            quote.timestamp
            for quote in quotes
        }

        if len(quote_timestamps) != 1:
            raise RuntimeError(
                "Latest quote batch contains multiple "
                "timestamps."
            )

        quote_timestamp = next(
            iter(quote_timestamps)
        )

        expected_count = context.get(
            "quotes_inserted"
        )

        if (
            expected_count is not None
            and len(quotes) != expected_count
        ):
            raise RuntimeError(
                "Snapshot quote count does not match "
                "the collector output. "
                f"Collector: {expected_count}, "
                f"Snapshot input: {len(quotes)}"
            )

        snapshot_time = datetime.now()

        snapshots = [
            ScannerSnapshot(
                run_id=run_id,
                symbol=quote.symbol,
                spot_price=quote.spot_price,
                volume=quote.volume,
                underlying_oi=quote.oi,
                source_quote_timestamp=(
                    quote.timestamp
                ),
                snapshot_time=snapshot_time,
            )
            for quote in quotes
        ]

        self.snapshot_repository.start_run(
            run_id=run_id,
            started_at=started_at,
            quote_timestamp=quote_timestamp,
            instrument_count=len(quotes),
        )

        inserted_count = (
            self.snapshot_repository
            .bulk_insert(snapshots)
        )

        persisted_count = (
            self.snapshot_repository
            .count_for_run(run_id)
        )

        if inserted_count != len(snapshots):
            raise RuntimeError(
                "Snapshot insert count validation failed. "
                f"Expected: {len(snapshots)}, "
                f"Inserted: {inserted_count}"
            )

        if persisted_count != len(quotes):
            raise RuntimeError(
                "Snapshot persistence validation failed. "
                f"Expected: {len(quotes)}, "
                f"Persisted: {persisted_count}"
            )

        self.snapshot_repository.complete_run(
            run_id=run_id,
            completed_at=datetime.now(),
            snapshot_count=persisted_count,
        )

        context["snapshot_complete"] = True
        context["snapshot_count"] = persisted_count
        context["snapshot_time"] = snapshot_time
        context["source_quote_timestamp"] = (
            quote_timestamp
        )
        context["stage_metric_data"] = {
            "records_requested": len(quotes),
            "records_received": len(quotes),
            "records_written": persisted_count,
            "source_timestamp": quote_timestamp,
        }

        print(f"Run ID: {run_id}")
        print(
            "Source quote timestamp: "
            f"{quote_timestamp}"
        )
        print(
            f"Snapshots prepared: {len(snapshots)}"
        )
        print(
            f"Snapshots persisted: {persisted_count}"
        )
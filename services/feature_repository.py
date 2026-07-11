from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from services.database import get_connection


@dataclass(frozen=True)
class FeatureInput:
    symbol: str
    spot_price: float
    volume: int | None
    previous_spot_price: float | None
    previous_volume: int | None
    average_prior_volume: float | None
    history_count: int


@dataclass(frozen=True)
class MarketFeature:
    run_id: str
    symbol: str
    spot_price: float
    previous_spot_price: float | None
    price_change: float | None
    price_change_pct: float | None
    volume: int | None
    previous_volume: int | None
    volume_change: int | None
    volume_change_pct: float | None
    average_prior_volume: float | None
    relative_volume: float | None
    history_count: int
    calculated_at: datetime


class FeatureRepository:
    def list_inputs_for_run(
        self,
        run_id: str,
        lookback_runs: int = 20,
    ) -> list[FeatureInput]:
        if lookback_runs <= 0:
            raise ValueError(
                "lookback_runs must be greater than zero."
            )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        current_snapshot.symbol,
                        current_snapshot.spot_price,
                        current_snapshot.volume,
                        previous_snapshot.spot_price,
                        previous_snapshot.volume,
                        volume_history.average_prior_volume,
                        volume_history.history_count
                    FROM scanner_snapshots current_snapshot

                    LEFT JOIN LATERAL
                    (
                        SELECT
                            history.spot_price,
                            history.volume
                        FROM scanner_snapshots history
                        WHERE history.symbol =
                            current_snapshot.symbol
                          AND history.run_id <>
                            current_snapshot.run_id
                          AND history.snapshot_time <
                            current_snapshot.snapshot_time
                        ORDER BY history.snapshot_time DESC
                        LIMIT 1
                    ) previous_snapshot
                    ON TRUE

                    LEFT JOIN LATERAL
                    (
                        SELECT
                            AVG(recent_history.volume)
                                AS average_prior_volume,
                            COUNT(*)
                                AS history_count
                        FROM
                        (
                            SELECT history.volume
                            FROM scanner_snapshots history
                            WHERE history.symbol =
                                current_snapshot.symbol
                              AND history.run_id <>
                                current_snapshot.run_id
                              AND history.snapshot_time <
                                current_snapshot.snapshot_time
                              AND history.volume IS NOT NULL
                            ORDER BY
                                history.snapshot_time DESC
                            LIMIT %s
                        ) recent_history
                    ) volume_history
                    ON TRUE

                    WHERE current_snapshot.run_id = %s
                    ORDER BY current_snapshot.symbol;
                    """,
                    (
                        lookback_runs,
                        run_id,
                    ),
                )

                rows = cursor.fetchall()

        return [
            FeatureInput(
                symbol=str(row[0]).strip().upper(),
                spot_price=float(row[1]),
                volume=(
                    int(row[2])
                    if row[2] is not None
                    else None
                ),
                previous_spot_price=(
                    float(row[3])
                    if row[3] is not None
                    else None
                ),
                previous_volume=(
                    int(row[4])
                    if row[4] is not None
                    else None
                ),
                average_prior_volume=(
                    float(row[5])
                    if row[5] is not None
                    else None
                ),
                history_count=int(row[6] or 0),
            )
            for row in rows
        ]

    def bulk_upsert(
        self,
        features: Iterable[MarketFeature],
    ) -> int:
        records = [
            (
                feature.run_id,
                feature.symbol,
                feature.spot_price,
                feature.previous_spot_price,
                feature.price_change,
                feature.price_change_pct,
                feature.volume,
                feature.previous_volume,
                feature.volume_change,
                feature.volume_change_pct,
                feature.average_prior_volume,
                feature.relative_volume,
                feature.history_count,
                feature.calculated_at,
            )
            for feature in features
        ]

        if not records:
            return 0

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO market_features
                    (
                        run_id,
                        symbol,
                        spot_price,
                        previous_spot_price,
                        price_change,
                        price_change_pct,
                        volume,
                        previous_volume,
                        volume_change,
                        volume_change_pct,
                        average_prior_volume,
                        relative_volume,
                        history_count,
                        calculated_at
                    )
                    VALUES
                    (
                        %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (run_id, symbol)
                    DO UPDATE SET
                        spot_price = EXCLUDED.spot_price,
                        previous_spot_price =
                            EXCLUDED.previous_spot_price,
                        price_change =
                            EXCLUDED.price_change,
                        price_change_pct =
                            EXCLUDED.price_change_pct,
                        volume = EXCLUDED.volume,
                        previous_volume =
                            EXCLUDED.previous_volume,
                        volume_change =
                            EXCLUDED.volume_change,
                        volume_change_pct =
                            EXCLUDED.volume_change_pct,
                        average_prior_volume =
                            EXCLUDED.average_prior_volume,
                        relative_volume =
                            EXCLUDED.relative_volume,
                        history_count =
                            EXCLUDED.history_count,
                        calculated_at =
                            EXCLUDED.calculated_at;
                    """,
                    records,
                )

            connection.commit()

        return len(records)

    def count_for_run(
        self,
        run_id: str,
    ) -> int:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM market_features
                    WHERE run_id = %s;
                    """,
                    (run_id,),
                )

                result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Unable to count features for run: {run_id}"
            )

        return int(result[0])

    def complete_run(
        self,
        run_id: str,
        feature_count: int,
        completed_at: datetime,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE pipeline_runs
                    SET
                        status = %s,
                        feature_count = %s,
                        completed_at = %s
                    WHERE run_id = %s;
                    """,
                    (
                        "FEATURE_COMPLETE",
                        feature_count,
                        completed_at,
                        run_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Unable to update pipeline run: "
                        f"{run_id}"
                    )

            connection.commit()
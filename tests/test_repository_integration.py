import os
import unittest
from datetime import datetime, timedelta
from uuid import uuid4

from services.database import get_connection
from services.feature_repository import (
    FeatureRepository,
    MarketFeature,
)
from services.instrument_repository import (
    Instrument,
    InstrumentRepository,
)
from services.snapshot_repository import (
    ScannerSnapshot,
    SnapshotRepository,
)
from services.underlying_quote_repository import (
    UnderlyingQuoteRepository,
)


RUN_INTEGRATION_TESTS = (
    os.getenv(
        "RUN_DB_INTEGRATION_TESTS",
        "0",
    )
    == "1"
)


@unittest.skipUnless(
    RUN_INTEGRATION_TESTS,
    "Set RUN_DB_INTEGRATION_TESTS=1 "
    "to run PostgreSQL integration tests.",
)
class RepositoryIntegrationTest(
    unittest.TestCase
):
    def setUp(self) -> None:
        suffix = uuid4().hex[:8].upper()

        self.symbol = f"ZZTEST{suffix}"
        self.run_id = str(uuid4())
        self.quote_timestamp = (
            datetime.now()
            + timedelta(days=1)
        )
        self.snapshot_time = datetime.now()

    def tearDown(self) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM market_features
                    WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM scanner_snapshots
                    WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM pipeline_runs
                    WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )

                cursor.execute(
                    """
                    DELETE FROM underlying_quotes
                    WHERE symbol = %s;
                    """,
                    (self.symbol,),
                )

                cursor.execute(
                    """
                    DELETE FROM instruments
                    WHERE symbol = %s;
                    """,
                    (self.symbol,),
                )

            connection.commit()

    def test_instrument_repository_upsert(
        self,
    ) -> None:
        repository = InstrumentRepository()

        inserted = repository.bulk_upsert(
            [
                Instrument(
                    symbol=self.symbol,
                    exchange="NSE_EQ",
                    security_id="99999991",
                    instrument_type="EQUITY",
                    lot_size=25,
                    tick_size=0.05,
                )
            ]
        )

        instruments = (
            repository
            .list_active_quote_instruments()
        )

        matches = [
            instrument
            for instrument in instruments
            if instrument.symbol == self.symbol
        ]

        self.assertEqual(inserted, 1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(
            matches[0].security_id,
            "99999991",
        )
        self.assertEqual(
            matches[0].lot_size,
            25,
        )

    def test_latest_quote_repository(
        self,
    ) -> None:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO underlying_quotes
                    (
                        symbol,
                        spot_price,
                        volume,
                        oi,
                        timestamp
                    )
                    VALUES
                    (%s, %s, %s, %s, %s);
                    """,
                    (
                        self.symbol,
                        100.50,
                        1000,
                        500,
                        self.quote_timestamp,
                    ),
                )

            connection.commit()

        repository = (
            UnderlyingQuoteRepository()
        )

        latest_timestamp = (
            repository
            .latest_batch_timestamp()
        )

        quotes = (
            repository
            .list_latest_batch()
        )

        matches = [
            quote
            for quote in quotes
            if quote.symbol == self.symbol
        ]

        self.assertEqual(
            latest_timestamp,
            self.quote_timestamp,
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(
            matches[0].spot_price,
            100.50,
        )
        self.assertEqual(
            matches[0].volume,
            1000,
        )

    def test_snapshot_and_feature_repositories(
        self,
    ) -> None:
        snapshot_repository = (
            SnapshotRepository()
        )

        snapshot_repository.start_run(
            run_id=self.run_id,
            started_at=self.snapshot_time,
            quote_timestamp=(
                self.quote_timestamp
            ),
            instrument_count=1,
        )

        inserted_snapshots = (
            snapshot_repository.bulk_insert(
                [
                    ScannerSnapshot(
                        run_id=self.run_id,
                        symbol=self.symbol,
                        spot_price=100.50,
                        volume=1000,
                        underlying_oi=500,
                        source_quote_timestamp=(
                            self.quote_timestamp
                        ),
                        snapshot_time=(
                            self.snapshot_time
                        ),
                    )
                ]
            )
        )

        snapshot_count = (
            snapshot_repository.count_for_run(
                self.run_id
            )
        )

        snapshot_repository.complete_run(
            run_id=self.run_id,
            completed_at=datetime.now(),
            snapshot_count=snapshot_count,
        )

        feature_repository = (
            FeatureRepository()
        )

        inserted_features = (
            feature_repository.bulk_upsert(
                [
                    MarketFeature(
                        run_id=self.run_id,
                        symbol=self.symbol,
                        spot_price=100.50,
                        previous_spot_price=100.00,
                        price_change=0.50,
                        price_change_pct=0.50,
                        volume=1000,
                        previous_volume=800,
                        volume_change=200,
                        volume_change_pct=25.00,
                        average_prior_volume=900.00,
                        relative_volume=(
                            1000 / 900
                        ),
                        history_count=5,
                        calculated_at=datetime.now(),
                    )
                ]
            )
        )

        feature_count = (
            feature_repository.count_for_run(
                self.run_id
            )
        )

        feature_repository.complete_run(
            run_id=self.run_id,
            feature_count=feature_count,
            completed_at=datetime.now(),
        )

        self.assertEqual(
            inserted_snapshots,
            1,
        )
        self.assertEqual(
            snapshot_count,
            1,
        )
        self.assertEqual(
            inserted_features,
            1,
        )
        self.assertEqual(
            feature_count,
            1,
        )

        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        status,
                        snapshot_count,
                        feature_count
                    FROM pipeline_runs
                    WHERE run_id = %s;
                    """,
                    (self.run_id,),
                )

                result = cursor.fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(
            result[0],
            "FEATURE_COMPLETE",
        )
        self.assertEqual(result[1], 1)
        self.assertEqual(result[2], 1)


if __name__ == "__main__":
    unittest.main()
import unittest
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from services.market_calendar import MarketCalendar
from services.scheduler import PipelineScheduler
from services.scheduler_models import SchedulerLock


TIMEZONE = ZoneInfo("Asia/Kolkata")


class FakePipeline:
    def __init__(
        self,
        should_fail: bool = False,
    ) -> None:
        self.started = False
        self.should_fail = should_fail

    def start(self) -> None:
        self.started = True

        if self.should_fail:
            raise RuntimeError("Pipeline failed")


class FakeSchedulerRepository:
    def __init__(self) -> None:
        self.lock: SchedulerLock | None = None
        self.released = False

    def acquire(
        self,
        lock_name,
        owner_token,
        acquired_at,
        ttl_seconds,
    ) -> bool:
        if (
            self.lock is not None
            and self.lock.expires_at > acquired_at
        ):
            return False

        self.lock = SchedulerLock(
            lock_name=lock_name,
            owner_token=owner_token,
            acquired_at=acquired_at,
            heartbeat_at=acquired_at,
            expires_at=(
                acquired_at
                + timedelta(seconds=ttl_seconds)
            ),
        )
        return True

    def heartbeat(
        self,
        lock_name,
        owner_token,
        heartbeat_at,
        ttl_seconds,
    ) -> bool:
        if (
            self.lock is None
            or self.lock.lock_name != lock_name
            or self.lock.owner_token != owner_token
        ):
            return False

        self.lock = SchedulerLock(
            lock_name=self.lock.lock_name,
            owner_token=self.lock.owner_token,
            acquired_at=self.lock.acquired_at,
            heartbeat_at=heartbeat_at,
            expires_at=(
                heartbeat_at
                + timedelta(seconds=ttl_seconds)
            ),
        )
        return True

    def release(
        self,
        lock_name,
        owner_token,
    ) -> bool:
        if (
            self.lock is None
            or self.lock.lock_name != lock_name
            or self.lock.owner_token != owner_token
        ):
            return False

        self.lock = None
        self.released = True
        return True

    def get(self, lock_name):
        if (
            self.lock is not None
            and self.lock.lock_name == lock_name
        ):
            return self.lock

        return None


class SchedulerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.calendar = MarketCalendar(
            timezone=TIMEZONE,
            open_time=time(9, 15),
            close_time=time(15, 30),
            holidays=frozenset(
                {date(2026, 8, 17)}
            ),
        )

    def test_market_open_during_session(self) -> None:
        status = self.calendar.status(
            datetime(
                2026,
                7,
                13,
                10,
                0,
                tzinfo=TIMEZONE,
            )
        )

        self.assertTrue(status.allowed)
        self.assertEqual(
            status.reason,
            "market session open",
        )

    def test_weekend_is_blocked(self) -> None:
        status = self.calendar.status(
            datetime(
                2026,
                7,
                12,
                10,
                0,
                tzinfo=TIMEZONE,
            )
        )

        self.assertFalse(status.allowed)
        self.assertEqual(status.reason, "weekend")

    def test_exchange_holiday_is_blocked(self) -> None:
        status = self.calendar.status(
            datetime(
                2026,
                8,
                17,
                10,
                0,
                tzinfo=TIMEZONE,
            )
        )

        self.assertFalse(status.allowed)
        self.assertIn("holiday", status.reason)

    def test_outside_market_hours_is_blocked(self) -> None:
        before_open = self.calendar.status(
            datetime(
                2026,
                7,
                13,
                8,
                0,
                tzinfo=TIMEZONE,
            )
        )
        after_close = self.calendar.status(
            datetime(
                2026,
                7,
                13,
                16,
                0,
                tzinfo=TIMEZONE,
            )
        )

        self.assertEqual(
            before_open.reason,
            "before market open",
        )
        self.assertEqual(
            after_close.reason,
            "after market close",
        )

    def test_scheduler_skips_closed_market(self) -> None:
        pipeline = FakePipeline()
        repository = FakeSchedulerRepository()
        scheduler = PipelineScheduler(
            pipeline_factory=lambda: pipeline,
            calendar=self.calendar,
            repository=repository,
            lock_name="test-lock",
            lock_ttl_seconds=60,
        )

        result = scheduler.run_once(
            moment=datetime(
                2026,
                7,
                12,
                10,
                0,
                tzinfo=TIMEZONE,
            )
        )

        self.assertEqual(result.status, "SKIPPED")
        self.assertFalse(pipeline.started)
        self.assertIsNone(repository.lock)

    def test_force_bypasses_calendar_only(self) -> None:
        pipeline = FakePipeline()
        repository = FakeSchedulerRepository()
        scheduler = PipelineScheduler(
            pipeline_factory=lambda: pipeline,
            calendar=self.calendar,
            repository=repository,
            lock_name="test-lock",
            lock_ttl_seconds=60,
        )

        result = scheduler.run_once(
            force=True,
            moment=datetime(
                2026,
                7,
                12,
                10,
                0,
                tzinfo=TIMEZONE,
            ),
        )

        self.assertEqual(result.status, "COMPLETED")
        self.assertTrue(pipeline.started)
        self.assertTrue(repository.released)

    def test_active_lock_prevents_overlap(self) -> None:
        pipeline = FakePipeline()
        repository = FakeSchedulerRepository()
        now = datetime(2026, 7, 13, 10, 0)
        repository.lock = SchedulerLock(
            lock_name="test-lock",
            owner_token="existing-owner",
            acquired_at=now,
            heartbeat_at=now,
            expires_at=now + timedelta(minutes=10),
        )
        scheduler = PipelineScheduler(
            pipeline_factory=lambda: pipeline,
            calendar=self.calendar,
            repository=repository,
            lock_name="test-lock",
            lock_ttl_seconds=60,
        )

        result = scheduler.run_once(
            moment=now.replace(tzinfo=TIMEZONE)
        )

        self.assertEqual(result.status, "SKIPPED")
        self.assertEqual(
            result.reason,
            "active run lock",
        )
        self.assertFalse(pipeline.started)

    def test_stale_lock_is_recovered(self) -> None:
        pipeline = FakePipeline()
        repository = FakeSchedulerRepository()
        now = datetime(2026, 7, 13, 10, 0)
        repository.lock = SchedulerLock(
            lock_name="test-lock",
            owner_token="stale-owner",
            acquired_at=now - timedelta(hours=1),
            heartbeat_at=now - timedelta(hours=1),
            expires_at=now - timedelta(minutes=30),
        )
        scheduler = PipelineScheduler(
            pipeline_factory=lambda: pipeline,
            calendar=self.calendar,
            repository=repository,
            lock_name="test-lock",
            lock_ttl_seconds=60,
        )

        result = scheduler.run_once(
            moment=now.replace(tzinfo=TIMEZONE)
        )

        self.assertEqual(result.status, "COMPLETED")
        self.assertTrue(pipeline.started)
        self.assertTrue(repository.released)

    def test_lock_released_when_pipeline_fails(self) -> None:
        pipeline = FakePipeline(should_fail=True)
        repository = FakeSchedulerRepository()
        scheduler = PipelineScheduler(
            pipeline_factory=lambda: pipeline,
            calendar=self.calendar,
            repository=repository,
            lock_name="test-lock",
            lock_ttl_seconds=60,
        )

        with self.assertRaises(RuntimeError):
            scheduler.run_once(
                moment=datetime(
                    2026,
                    7,
                    13,
                    10,
                    0,
                    tzinfo=TIMEZONE,
                )
            )

        self.assertTrue(repository.released)
        self.assertIsNone(repository.lock)


if __name__ == "__main__":
    unittest.main()

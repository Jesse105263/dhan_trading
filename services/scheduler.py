import logging
import threading
from collections.abc import Callable
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from services.market_calendar import (
    MarketCalendar,
    MarketSessionStatus,
)
from services.scheduler_models import SchedulerLock


class RunnablePipeline(Protocol):
    def start(self) -> None:
        ...


class SchedulerLockRepository(Protocol):
    def acquire(
        self,
        lock_name: str,
        owner_token: str,
        acquired_at: datetime,
        ttl_seconds: int,
    ) -> bool:
        ...

    def heartbeat(
        self,
        lock_name: str,
        owner_token: str,
        heartbeat_at: datetime,
        ttl_seconds: int,
    ) -> bool:
        ...

    def release(
        self,
        lock_name: str,
        owner_token: str,
    ) -> bool:
        ...

    def get(
        self,
        lock_name: str,
    ) -> SchedulerLock | None:
        ...


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SchedulerRunResult:
    status: str
    reason: str
    owner_token: str | None = None


@dataclass(frozen=True)
class SchedulerStatus:
    market: MarketSessionStatus
    lock: SchedulerLock | None
    lock_is_stale: bool


class PipelineScheduler:
    def __init__(
        self,
        pipeline_factory: Callable[[], RunnablePipeline],
        calendar: MarketCalendar,
        repository: SchedulerLockRepository,
        lock_name: str,
        lock_ttl_seconds: int,
    ) -> None:
        self.pipeline_factory = pipeline_factory
        self.calendar = calendar
        self.repository = repository
        self.lock_name = lock_name
        self.lock_ttl_seconds = lock_ttl_seconds

    def run_once(
        self,
        force: bool = False,
        moment: datetime | None = None,
    ) -> SchedulerRunResult:
        market_status = self.calendar.status(moment)

        if not force and not market_status.allowed:
            logger.info(
                "Scheduled run skipped | reason=%s",
                market_status.reason,
            )

            return SchedulerRunResult(
                status="SKIPPED",
                reason=market_status.reason,
            )

        owner_token = str(uuid4())
        acquired_at = market_status.checked_at.replace(
            tzinfo=None
        )

        acquired = self.repository.acquire(
            lock_name=self.lock_name,
            owner_token=owner_token,
            acquired_at=acquired_at,
            ttl_seconds=self.lock_ttl_seconds,
        )

        if not acquired:
            logger.warning(
                "Scheduled run skipped | reason=active run lock"
            )

            return SchedulerRunResult(
                status="SKIPPED",
                reason="active run lock",
            )

        logger.info(
            "Scheduler lock acquired | lock=%s | owner=%s",
            self.lock_name,
            owner_token,
        )

        stop_heartbeat = threading.Event()
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(owner_token, stop_heartbeat),
            name="scheduler-lock-heartbeat",
            daemon=True,
        )
        heartbeat_thread.start()

        try:
            pipeline = self.pipeline_factory()
            pipeline.start()
        except Exception:
            logger.exception(
                "Scheduled pipeline run failed | owner=%s",
                owner_token,
            )
            raise
        finally:
            stop_heartbeat.set()
            heartbeat_thread.join(
                timeout=max(1.0, self._heartbeat_interval_seconds())
            )

            released = self.repository.release(
                lock_name=self.lock_name,
                owner_token=owner_token,
            )

            if released:
                logger.info(
                    "Scheduler lock released | lock=%s | owner=%s",
                    self.lock_name,
                    owner_token,
                )
            else:
                logger.error(
                    "Scheduler lock release failed | lock=%s | owner=%s",
                    self.lock_name,
                    owner_token,
                )

        reason = (
            "manual override"
            if force
            else market_status.reason
        )

        return SchedulerRunResult(
            status="COMPLETED",
            reason=reason,
            owner_token=owner_token,
        )


    def _heartbeat_loop(
        self,
        owner_token: str,
        stop_event: threading.Event,
    ) -> None:
        interval = self._heartbeat_interval_seconds()

        while not stop_event.wait(interval):
            heartbeat_at = datetime.now(
                self.calendar.timezone
            ).replace(tzinfo=None)

            try:
                updated = self.repository.heartbeat(
                    lock_name=self.lock_name,
                    owner_token=owner_token,
                    heartbeat_at=heartbeat_at,
                    ttl_seconds=self.lock_ttl_seconds,
                )
            except Exception:
                logger.exception(
                    "Scheduler lock heartbeat failed | "
                    "lock=%s | owner=%s",
                    self.lock_name,
                    owner_token,
                )
                continue

            if not updated:
                logger.error(
                    "Scheduler lock ownership lost | "
                    "lock=%s | owner=%s",
                    self.lock_name,
                    owner_token,
                )
                return

    def _heartbeat_interval_seconds(self) -> float:
        return float(
            max(1, min(60, self.lock_ttl_seconds // 3))
        )

    def status(
        self,
        moment: datetime | None = None,
    ) -> SchedulerStatus:
        market_status = self.calendar.status(moment)
        lock = self.repository.get(self.lock_name)

        now = market_status.checked_at.replace(
            tzinfo=None
        )

        return SchedulerStatus(
            market=market_status,
            lock=lock,
            lock_is_stale=(
                lock.is_stale(now)
                if lock is not None
                else False
            ),
        )

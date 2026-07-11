from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SchedulerLock:
    lock_name: str
    owner_token: str
    acquired_at: datetime
    heartbeat_at: datetime
    expires_at: datetime

    def is_stale(
        self,
        now: datetime,
    ) -> bool:
        return self.expires_at <= now

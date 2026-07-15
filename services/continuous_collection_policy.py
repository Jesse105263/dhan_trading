from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class CollectionSession:
    name: str
    trading_day: bool
    expiry_day: bool
    reason: str


class ContinuousCollectionPolicy:
    """Deterministic NSE-style session policy; holidays are explicit inputs."""

    def __init__(self, holidays: frozenset[date] = frozenset(), timezone: ZoneInfo = ZoneInfo("Asia/Kolkata")):
        self.holidays = holidays
        self.timezone = timezone

    def classify(self, moment: datetime, expiries: frozenset[date] = frozenset()) -> CollectionSession:
        local = moment.replace(tzinfo=self.timezone) if moment.tzinfo is None else moment.astimezone(self.timezone)
        day = local.date()
        if local.weekday() >= 5:
            return CollectionSession("NON_TRADING", False, False, "weekend")
        if day in self.holidays:
            return CollectionSession("NON_TRADING", False, False, "exchange holiday")
        clock = local.timetz().replace(tzinfo=None)
        if clock < time(9, 0):
            name = "PRE_OPEN"
        elif clock < time(9, 15):
            name = "PRE_OPEN"
        elif clock < time(15, 30):
            name = "REGULAR"
        elif clock < time(15, 40):
            name = "CLOSE"
        else:
            name = "POST_CLOSE"
        expiry = day in expiries
        return CollectionSession(name, True, expiry, "expiry day" if expiry else "trading day")

    @staticmethod
    def permits_dataset(session: CollectionSession, dataset_type: str) -> bool:
        if not session.trading_day:
            return False
        allowed = {
            "PRE_OPEN": {"INSTRUMENT_MASTER", "CORPORATE_ACTIONS", "EVENTS_ANNOUNCEMENTS"},
            "REGULAR": {"UNDERLYING_BARS", "INDEX_BARS", "FUTURES_BARS", "OPTION_CONTRACT_BARS", "OPTION_CHAIN_SNAPSHOTS", "QUOTE_DEPTH_SNAPSHOTS", "EVENTS_ANNOUNCEMENTS"},
            "CLOSE": {"UNDERLYING_BARS", "INDEX_BARS", "FUTURES_BARS", "OPTION_CONTRACT_BARS", "OPTION_CHAIN_SNAPSHOTS", "QUOTE_DEPTH_SNAPSHOTS"},
            "POST_CLOSE": {"INSTRUMENT_MASTER", "UNDERLYING_BARS", "INDEX_BARS", "FUTURES_BARS", "OPTION_CONTRACT_BARS", "CORPORATE_ACTIONS", "EVENTS_ANNOUNCEMENTS"},
        }
        return dataset_type in allowed[session.name]

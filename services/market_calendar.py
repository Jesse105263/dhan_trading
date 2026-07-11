from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MarketSessionStatus:
    allowed: bool
    reason: str
    checked_at: datetime


class MarketCalendar:
    def __init__(
        self,
        timezone: ZoneInfo,
        open_time: time,
        close_time: time,
        holidays: frozenset[date],
    ) -> None:
        if close_time <= open_time:
            raise ValueError(
                "Market close time must be later than open time."
            )

        self.timezone = timezone
        self.open_time = open_time
        self.close_time = close_time
        self.holidays = holidays

    def status(
        self,
        moment: datetime | None = None,
    ) -> MarketSessionStatus:
        checked_at = self._normalize(moment)
        trading_date = checked_at.date()

        if checked_at.weekday() >= 5:
            return MarketSessionStatus(
                allowed=False,
                reason="weekend",
                checked_at=checked_at,
            )

        if trading_date in self.holidays:
            return MarketSessionStatus(
                allowed=False,
                reason="exchange holiday",
                checked_at=checked_at,
            )

        local_time = checked_at.timetz().replace(
            tzinfo=None
        )

        if local_time < self.open_time:
            return MarketSessionStatus(
                allowed=False,
                reason="before market open",
                checked_at=checked_at,
            )

        if local_time > self.close_time:
            return MarketSessionStatus(
                allowed=False,
                reason="after market close",
                checked_at=checked_at,
            )

        return MarketSessionStatus(
            allowed=True,
            reason="market session open",
            checked_at=checked_at,
        )

    def _normalize(
        self,
        moment: datetime | None,
    ) -> datetime:
        if moment is None:
            return datetime.now(self.timezone)

        if moment.tzinfo is None:
            return moment.replace(
                tzinfo=self.timezone
            )

        return moment.astimezone(self.timezone)

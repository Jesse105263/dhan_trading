from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable

from services.alert_channels import AlertChannel
from services.alert_models import AlertRunResult, SOURCE_TYPES
from services.error_sanitizer import sanitize_error_message


class AlertService:
    def __init__(self, repository, clock: Callable[[], datetime] = datetime.now) -> None:
        self.repository = repository
        self.clock = clock

    def generate_and_deliver(
        self,
        source_types: Iterable[str],
        channels: Iterable[AlertChannel],
        limit: int = 100,
    ) -> AlertRunResult:
        normalized_sources = tuple(dict.fromkeys(value.strip().upper() for value in source_types))
        unknown = set(normalized_sources) - SOURCE_TYPES
        if unknown:
            raise ValueError(f"Unsupported alert source type: {sorted(unknown)[0]}")
        if not normalized_sources:
            raise ValueError("At least one alert source type is required.")
        if not 1 <= limit <= 1000:
            raise ValueError("Alert limit must be between 1 and 1000.")
        normalized_channels = tuple(channels)
        channel_names = [channel.name.strip().lower() for channel in normalized_channels]
        if any(not name for name in channel_names) or len(set(channel_names)) != len(channel_names):
            raise ValueError("Alert channel names must be non-empty and unique.")

        candidates = self.repository.list_candidates(normalized_sources, limit)
        created = duplicates = succeeded = failed = skipped = 0
        alert_ids = []
        for candidate in candidates:
            persisted = self.repository.ensure_alert(candidate, self.clock())
            alert = persisted.event
            alert_ids.append(alert.alert_id)
            created += int(persisted.created)
            duplicates += int(not persisted.created)
            for channel in normalized_channels:
                channel_name = channel.name.strip().lower()
                if self.repository.was_delivered(alert.alert_id, channel_name):
                    skipped += 1
                    continue
                attempt_id = self.repository.start_delivery(alert.alert_id, channel_name, self.clock())
                try:
                    channel.deliver(alert)
                except Exception as exc:
                    self.repository.finish_delivery(
                        attempt_id, False, self.clock(), sanitize_error_message(str(exc))
                    )
                    failed += 1
                else:
                    self.repository.finish_delivery(attempt_id, True, self.clock())
                    succeeded += 1
        return AlertRunResult(
            candidates_found=len(candidates), alerts_created=created,
            duplicate_alerts=duplicates, deliveries_succeeded=succeeded,
            deliveries_failed=failed, deliveries_skipped=skipped,
            alert_ids=tuple(alert_ids),
        )

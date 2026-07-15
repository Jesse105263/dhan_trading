from __future__ import annotations

import json
from typing import Protocol

from services.continuous_collection_models import CollectionWork, ProviderBatch


class ProviderUnavailableError(RuntimeError):
    pass


class ProviderQuotaExhaustedError(RuntimeError):
    pass


class ContinuousCollectionProvider(Protocol):
    provider_code: str

    def collect(self, work: CollectionWork) -> ProviderBatch:
        ...


class LocalFixtureCollectionProvider:
    """Bounded deterministic provider with no network or credential capability."""

    provider_code = "LOCAL_FIXTURE"

    def __init__(self, batches: dict[str, ProviderBatch | Exception]):
        self._batches = dict(batches)

    def collect(self, work: CollectionWork) -> ProviderBatch:
        value = self._batches.get(str(work.work_id), self._batches.get("*"))
        if value is None:
            raise ProviderUnavailableError("No local fixture is registered for work item.")
        if isinstance(value, Exception):
            raise value
        if len(value.payload) > 5_000_000:
            raise ValueError("Fixture payload exceeds the five-megabyte bound.")
        json.loads(value.payload.decode("utf-8"))
        return value

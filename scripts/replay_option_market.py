from __future__ import annotations
import argparse
from datetime import datetime
from uuid import UUID
from services.market_replay_models import MarketReplayRequest
from services.market_replay_repository import MarketReplayRepository
from services.market_replay_service import MarketReplayService


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay persisted option-market lineage.")
    parser.add_argument("signal_run_id", type=UUID)
    args = parser.parse_args()
    result = MarketReplayService(MarketReplayRepository()).replay_and_persist(
        MarketReplayRequest(signal_run_id=args.signal_run_id, as_of=datetime.now())
    )
    print("Market replay completed")
    print(f"Replay run ID: {result.replay_run_id}")
    print(f"Signal run ID: {result.signal_run_id}")
    print(f"Signals replayed: {result.signal_count}")
    print(f"Events persisted: {len(result.events)}")
    for event in result.events:
        print(f"{event.sequence_number}. {event.event_type} {event.underlying_symbol} {event.expiry} {event.option_type or '-'} entity={event.entity_id}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse

from services.feature_store_service import FeatureStoreService


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize versioned features from persisted market observations.")
    parser.add_argument("--limit", type=int)
    result = FeatureStoreService().materialize(parser.parse_args().limit)
    print(f"Feature store materialized | sources={result['source_count']} vectors={result['materialized_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

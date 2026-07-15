from __future__ import annotations

import json

from services.research_baseline import ResearchBaselineService


def main() -> int:
    report = ResearchBaselineService().report()
    print(json.dumps(report, default=str, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

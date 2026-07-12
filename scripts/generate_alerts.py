from __future__ import annotations

import argparse
import sys

from services.alert_channels import ConsoleAlertChannel, WebhookAlertChannel
from services.alert_repository import AlertRepository
from services.alert_service import AlertService


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate private alerts from persisted platform outputs.")
    parser.add_argument(
        "--source", action="append", choices=("signal", "risk", "pipeline"),
        help="Source to process; repeat as needed. Defaults to all sources.",
    )
    parser.add_argument("--channel", action="append", choices=("console", "webhook"), default=[])
    parser.add_argument("--webhook-url")
    parser.add_argument("--webhook-timeout", type=float, default=5.0)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    source_map = {"signal": "SIGNAL", "risk": "RISK_DECISION", "pipeline": "PIPELINE_HEALTH"}
    sources = tuple(source_map[value] for value in (args.source or source_map))
    channel_names = args.channel or ["console"]
    channels = []
    for name in channel_names:
        if name == "console":
            channels.append(ConsoleAlertChannel(sys.stdout))
        elif name == "webhook":
            if not args.webhook_url:
                parser.error("--webhook-url is required when --channel webhook is used")
            channels.append(WebhookAlertChannel(args.webhook_url, args.webhook_timeout))

    result = AlertService(AlertRepository()).generate_and_deliver(sources, channels, args.limit)
    print("Alert processing completed")
    print(f"Candidates found: {result.candidates_found}")
    print(f"Alerts created: {result.alerts_created}")
    print(f"Duplicates reused: {result.duplicate_alerts}")
    print(f"Deliveries succeeded: {result.deliveries_succeeded}")
    print(f"Deliveries failed: {result.deliveries_failed}")
    print(f"Deliveries skipped: {result.deliveries_skipped}")


if __name__ == "__main__":
    main()

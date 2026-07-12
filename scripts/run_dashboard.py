from __future__ import annotations

import argparse
from wsgiref.simple_server import make_server

from app.dashboard import DashboardApiClient, DashboardApplication


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the private read-only Dhan dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--api-timeout", type=float, default=5.0)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("port must be between 1 and 65535")
    if args.api_timeout <= 0:
        raise SystemExit("api-timeout must be greater than zero")
    application = DashboardApplication(DashboardApiClient(args.api_base_url, args.api_timeout))
    print(f"Private read-only dashboard listening on http://{args.host}:{args.port}")
    print(f"Consuming read API at {args.api_base_url.rstrip('/')}")
    with make_server(args.host, args.port, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()

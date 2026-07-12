from __future__ import annotations

import argparse
from wsgiref.simple_server import make_server

from app.read_api import application


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the read-only Dhan Trading Platform API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("port must be between 1 and 65535")
    print(f"Read-only API listening on http://{args.host}:{args.port}")
    with make_server(args.host, args.port, application) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()

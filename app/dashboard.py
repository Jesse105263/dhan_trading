from __future__ import annotations

import html
import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


RESOURCE_LABELS = {
    "rankings": "Rankings",
    "selections": "Contract selections",
    "risk": "Risk assessments",
    "signals": "Signals",
    "replays": "Market replays",
    "backtests": "Backtests",
}

RUN_ID_FIELDS = {
    "rankings": "ranking_run_id",
    "selections": "selection_run_id",
    "risk": "risk_run_id",
    "signals": "signal_run_id",
    "replays": "replay_run_id",
    "backtests": "backtest_run_id",
}


class DashboardApiError(RuntimeError):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class DashboardApiClient:
    """HTTP-only client for the stable read API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def health(self) -> dict[str, Any]:
        return self._get("/health")

    def list_runs(self, resource: str, limit: int = 20) -> dict[str, Any]:
        self._validate_resource(resource)
        return self._get(f"/api/v1/{resource}?limit={limit}")

    def get_run(self, resource: str, run_id: str) -> dict[str, Any]:
        self._validate_resource(resource)
        return self._get(f"/api/v1/{resource}/{quote(run_id, safe='')}")

    def _get(self, path: str) -> dict[str, Any]:
        request = Request(self.base_url + path, method="GET", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            try:
                message = self._http_error_message(exc)
            finally:
                exc.close()
            raise DashboardApiError(message, exc.code) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise DashboardApiError("The read API is unavailable. Check that it is running locally.") from exc
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DashboardApiError("The read API returned an invalid JSON response.") from exc
        if not isinstance(value, dict):
            raise DashboardApiError("The read API returned an unexpected response.")
        return value

    @staticmethod
    def _http_error_message(error: HTTPError) -> str:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            return str(payload["error"]["message"])
        except (KeyError, TypeError, ValueError, UnicodeDecodeError):
            return f"The read API returned HTTP {error.code}."

    @staticmethod
    def _validate_resource(resource: str) -> None:
        if resource not in RESOURCE_LABELS:
            raise ValueError(f"Unsupported dashboard resource: {resource}")


@dataclass(frozen=True)
class DashboardResponse:
    status: HTTPStatus
    body: str


class DashboardApplication:
    def __init__(self, client: DashboardApiClient | None = None) -> None:
        self.client = client or DashboardApiClient()

    def handle(self, method: str, path: str) -> DashboardResponse:
        if method.upper() != "GET":
            return self._page(HTTPStatus.METHOD_NOT_ALLOWED, "Read only", self._state("error", "Only GET is supported."))
        normalized = path.rstrip("/") or "/"
        if normalized == "/":
            return self._overview()
        parts = normalized.strip("/").split("/")
        if parts[0] != "dashboard" or len(parts) not in (2, 3) or parts[1] not in RESOURCE_LABELS:
            return self._page(HTTPStatus.NOT_FOUND, "Not found", self._state("empty", "Dashboard page not found."))
        resource = parts[1]
        return self._list(resource) if len(parts) == 2 else self._detail(resource, parts[2])

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        response = self.handle(str(environ.get("REQUEST_METHOD", "GET")), str(environ.get("PATH_INFO", "/")))
        payload = response.body.encode("utf-8")
        start_response(
            f"{response.status.value} {response.status.phrase}",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(payload))),
                ("Cache-Control", "no-store"),
                ("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'"),
                ("X-Content-Type-Options", "nosniff"),
                ("X-Frame-Options", "DENY"),
                ("Referrer-Policy", "no-referrer"),
            ],
        )
        return [payload]

    def _overview(self) -> DashboardResponse:
        sections: list[str] = []
        try:
            health = self.client.health()
            ready = health.get("status") == "ok" and health.get("database_ready") is True
            css_class = "healthy" if ready else "warning"
            message = "Read API and database are ready." if ready else "Read API responded, but the database is not ready."
            sections.append(f'<section class="health {css_class}"><span class="pulse"></span><div><strong>Platform health</strong><p>{html.escape(message)}</p></div></section>')
        except DashboardApiError as exc:
            sections.append(self._state("error", str(exc)))
        cards: list[str] = []
        for resource, label in RESOURCE_LABELS.items():
            try:
                payload = self.client.list_runs(resource, limit=5)
                count = int(payload.get("count", len(payload.get("data", []))))
                detail = f"{count} recent run{'s' if count != 1 else ''}"
            except (DashboardApiError, TypeError, ValueError):
                detail = "Unavailable"
            cards.append(f'<a class="resource-card" href="/dashboard/{resource}"><span>{html.escape(label)}</span><small>{html.escape(detail)}</small></a>')
        sections.append('<section><div class="section-heading"><div><p class="eyebrow">Persisted intelligence</p><h2>Research surfaces</h2></div></div><div class="resource-grid">' + "".join(cards) + "</div></section>")
        return self._page(HTTPStatus.OK, "Overview", "".join(sections))

    def _list(self, resource: str) -> DashboardResponse:
        label = RESOURCE_LABELS[resource]
        try:
            payload = self.client.list_runs(resource)
            rows = payload.get("data", [])
            if not isinstance(rows, list):
                raise DashboardApiError("The read API returned an unexpected collection.")
        except DashboardApiError as exc:
            return self._page(HTTPStatus.BAD_GATEWAY, label, self._state("error", str(exc)))
        if not rows:
            content = self._state("empty", f"No {label.lower()} are available yet.")
        else:
            content = self._table(rows, resource)
        heading = f'<div class="section-heading"><div><p class="eyebrow">Recent runs</p><h2>{html.escape(label)}</h2></div><span class="count">{len(rows)} shown</span></div>'
        return self._page(HTTPStatus.OK, label, heading + content)

    def _detail(self, resource: str, run_id: str) -> DashboardResponse:
        label = RESOURCE_LABELS[resource]
        try:
            payload = self.client.get_run(resource, run_id)
            data = payload.get("data")
            if not isinstance(data, dict):
                raise DashboardApiError("The read API returned an unexpected run detail.")
        except DashboardApiError as exc:
            status = HTTPStatus.NOT_FOUND if exc.status == HTTPStatus.NOT_FOUND else HTTPStatus.BAD_GATEWAY
            return self._page(status, label, self._state("empty" if status == HTTPStatus.NOT_FOUND else "error", str(exc)))
        items = data.get("items", [])
        run = {key: value for key, value in data.items() if key != "items"}
        heading = f'<div class="section-heading"><div><p class="eyebrow">Run detail</p><h2>{html.escape(label)}</h2></div><a class="back" href="/dashboard/{resource}">Back to runs</a></div>'
        content = heading + '<section class="run-summary"><h3>Summary</h3>' + self._definition_grid(run) + "</section>"
        if not isinstance(items, list) or not items:
            content += self._state("empty", "This run contains no child records.")
        elif resource == "replays":
            content += self._timeline(items)
        else:
            content += '<section><h3>Records</h3>' + self._table(items) + "</section>"
        return self._page(HTTPStatus.OK, label, content)

    def _table(self, rows: list[dict[str, Any]], resource: str | None = None) -> str:
        columns = list(dict.fromkeys(key for row in rows for key in row))
        head = "".join(f"<th>{self._label(key)}</th>" for key in columns)
        body_rows: list[str] = []
        for row in rows:
            cells: list[str] = []
            for key in columns:
                rendered = self._value(row.get(key))
                if resource and key == RUN_ID_FIELDS[resource] and row.get(key):
                    run_id = quote(str(row[key]), safe="")
                    rendered = f'<a class="run-link" href="/dashboard/{resource}/{run_id}">{rendered}</a>'
                cells.append(f"<td>{rendered}</td>")
            body_rows.append("<tr>" + "".join(cells) + "</tr>")
        return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'

    def _definition_grid(self, data: dict[str, Any]) -> str:
        return '<dl class="definition-grid">' + "".join(
            f"<div><dt>{self._label(key)}</dt><dd>{self._value(value)}</dd></div>" for key, value in data.items()
        ) + "</dl>"

    def _timeline(self, items: list[dict[str, Any]]) -> str:
        events = []
        for item in items:
            title = item.get("event_type", "Replay event")
            sequence = item.get("sequence_number", "—")
            events.append(f'<li><span class="sequence">{html.escape(str(sequence))}</span><div><h4>{html.escape(str(title))}</h4>{self._definition_grid(item)}</div></li>')
        return '<section><h3>Replay timeline</h3><ol class="timeline">' + "".join(events) + "</ol></section>"

    def _page(self, status: HTTPStatus, title: str, content: str) -> DashboardResponse:
        nav = "".join(f'<a href="/dashboard/{resource}">{html.escape(label)}</a>' for resource, label in RESOURCE_LABELS.items())
        document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Dhan Monitor</title><style>{self._styles()}</style></head>
<body><header><a class="brand" href="/"><span class="brand-mark">D</span><span>Dhan Monitor<small>PRIVATE · READ ONLY</small></span></a><nav>{nav}</nav></header>
<main><div class="hero"><p class="eyebrow">Decision intelligence</p><h1>{html.escape(title)}</h1><p>Auditable market research from persisted platform data.</p></div>{content}</main>
<footer>No execution · No broker calls · Data supplied only by the /api/v1 read API</footer></body></html>'''
        return DashboardResponse(status, document)

    @staticmethod
    def _state(kind: str, message: str) -> str:
        return f'<section class="state {kind}"><strong>{"Unable to load data" if kind == "error" else "Nothing to show"}</strong><p>{html.escape(message)}</p></section>'

    @staticmethod
    def _label(value: str) -> str:
        return html.escape(value.replace("_", " ").title())

    @staticmethod
    def _value(value: Any) -> str:
        if value is None:
            return '<span class="muted">—</span>'
        if isinstance(value, bool):
            return f'<span class="badge {"yes" if value else "no"}">{"Yes" if value else "No"}</span>'
        if isinstance(value, (dict, list)):
            return f"<pre>{html.escape(json.dumps(value, indent=2, sort_keys=True))}</pre>"
        text = str(value)
        if len(text) > 80:
            return f'<span class="wrap">{html.escape(text)}</span>'
        return html.escape(text)

    @staticmethod
    def _styles() -> str:
        return """
:root{--ink:#17211b;--muted:#68736c;--paper:#f4f1e9;--card:#fffdf7;--line:#dcd8cd;--green:#176b4b;--lime:#c9ef68;--red:#a63c32;--amber:#916116}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}header{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:18px max(24px,5vw);border-bottom:1px solid var(--line);background:rgba(255,253,247,.92)}a{color:inherit}.brand{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:750}.brand-mark{display:grid;place-items:center;width:36px;height:36px;border-radius:10px;background:var(--ink);color:var(--lime)}.brand small{display:block;color:var(--green);font-size:9px;letter-spacing:.15em}nav{display:flex;gap:18px;overflow:auto}nav a{color:var(--muted);font-size:13px;text-decoration:none;white-space:nowrap}nav a:hover,.run-link{color:var(--green)}main{width:min(1480px,92vw);margin:auto;padding:44px 0 70px}.hero{margin-bottom:35px}.hero h1{font:700 clamp(34px,5vw,68px)/1.05 Georgia,serif;margin:5px 0 10px;letter-spacing:-.035em}.hero>p:last-child{color:var(--muted)}.eyebrow{color:var(--green);font-size:11px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;margin:0}.health,.state{display:flex;gap:14px;align-items:center;padding:20px 22px;border:1px solid var(--line);border-radius:16px;background:var(--card);margin:0 0 30px}.health p,.state p{margin:2px 0;color:var(--muted)}.pulse{width:12px;height:12px;border-radius:50%;background:var(--green);box-shadow:0 0 0 6px #176b4b18}.warning .pulse{background:var(--amber)}.state.error{border-color:#d9aaa5}.section-heading{display:flex;justify-content:space-between;align-items:end;gap:20px;margin:26px 0 14px}.section-heading h2{font:700 28px Georgia,serif;margin:3px 0}.count,.back{color:var(--muted);font-size:13px}.resource-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.resource-card{min-height:125px;padding:22px;border:1px solid var(--line);border-radius:16px;background:var(--card);text-decoration:none;display:flex;flex-direction:column;justify-content:space-between;font:700 19px Georgia,serif}.resource-card:hover{border-color:var(--green);transform:translateY(-2px)}.resource-card small{font:500 12px ui-sans-serif;color:var(--muted)}section h3{font:700 20px Georgia,serif}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:15px;background:var(--card)}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top;white-space:nowrap}th{position:sticky;top:0;background:#ece8dd;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.08em}td pre{max-width:360px}.run-summary{padding:22px;border:1px solid var(--line);border-radius:16px;background:var(--card);margin-bottom:25px}.definition-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin:0}.definition-grid>div{min-width:0;background:var(--card);padding:13px}.definition-grid dt{color:var(--muted);font-size:10px;text-transform:uppercase}.definition-grid dd{margin:4px 0;overflow-wrap:anywhere}.badge{padding:3px 8px;border-radius:99px;background:#e6e2d8}.badge.yes{color:var(--green)}.badge.no{color:var(--red)}pre{white-space:pre-wrap;margin:0;font:11px/1.4 ui-monospace,monospace}.timeline{list-style:none;padding:0}.timeline li{display:grid;grid-template-columns:42px 1fr;gap:15px;margin-bottom:12px}.timeline li>div{padding:18px;background:var(--card);border:1px solid var(--line);border-radius:14px}.timeline h4{margin:0 0 12px}.sequence{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:var(--ink);color:var(--lime);font-weight:800}.muted{color:var(--muted)}.wrap{white-space:normal;display:block;min-width:260px}footer{padding:24px;text-align:center;border-top:1px solid var(--line);color:var(--muted);font-size:11px}@media(max-width:900px){header{align-items:flex-start;flex-direction:column}nav{width:100%}.resource-grid{grid-template-columns:1fr 1fr}.definition-grid{grid-template-columns:1fr 1fr}}@media(max-width:600px){main{width:94vw;padding-top:28px}.resource-grid,.definition-grid{grid-template-columns:1fr}.hero h1{font-size:38px}}
"""


application = DashboardApplication()

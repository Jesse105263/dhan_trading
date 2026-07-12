# Dhan Trading Platform

Institutional-grade options trading and market intelligence platform.

## Stack

- Python
- Docker
- PostgreSQL
- Redis
- Dhan API

## Setup

1. Create virtual environment
2. Install requirements

```bash
pip install -r requirements.txt
```

3. Configure `.env`

4. Start Docker

```bash
docker compose up -d
```

## Documentation

See the `docs/` folder.

## Private Dashboard

Start the read API and dashboard in separate terminals:

```bash
python -m scripts.run_read_api
python -m scripts.run_dashboard
```

Open `http://127.0.0.1:8081`. The dashboard is read-only, local by default and obtains all platform data through `/api/v1` HTTP GET requests.

## Private Alerts

Generate deduplicated, auditable alerts from persisted signals, risk decisions and pipeline health:

```bash
python -m scripts.generate_alerts
```

See `docs/ALERTS.md` for source and channel configuration.

## Status

Under active development.

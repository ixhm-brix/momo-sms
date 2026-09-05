# MoMo SMS Data Analysis

Fullstack application that processes MTN MoMo SMS data from XML, cleans and
categorizes it, stores it in SQLite, and visualizes it on a dashboard.

## Team

| Name | Role |
|---|---|
| Fabrice | Repo & scaffolding |
| Lewis | Data & database |
| Ian | Frontend & data contract |
| Dana | Architecture & docs |
| Digne | Process & board |

## Links

- Architecture diagram: _TBD — Dana_
- Scrum board: _TBD — Digne_

## Setup

```bash
git clone <repo-url>
cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Place the provided `momo.xml` in `data/raw/`. It is git-ignored — each team
member obtains it separately and never commits it.

## Run

```bash
bash scripts/run_etl.sh        # parse -> clean -> categorize -> load -> export
bash scripts/serve_frontend.sh # then open http://localhost:8000
```

## Project structure

```
etl/      Parse, clean, categorize, load
data/     Raw XML, SQLite DB, processed JSON, logs
web/      Dashboard styles and scripts
api/      Optional FastAPI service
scripts/  Convenience runners
tests/    Unit tests
```

## Architecture

_TBD — Dana_

## Data model

_TBD — Lewis_

## Frontend

_TBD — Ian_

## Process

_TBD — Digne_

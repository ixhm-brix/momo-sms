# MoMo SMS Data Analysis

Fullstack application that is used processes MTN MoMo SMS data from XML, cleans and
categorizes it, stores it in SQLite, and easily visualizes it on a dashboard.

## Team

| Name | Role |
|---|---|
| Ishimwe Fabrice | Repo & scaffolding |
| Bagabo Lewis | Data & database |
|Kamuzinzi Ian | Frontend & data contract |
|Keza Dana | Architecture & docs |
| Nyange Digne | Process & board |

## Links

- ## Links

- Architecture diagram: [View on Miro]https://miro.com/app/board/uXjVHpncxSU=/?share_link_id=874764227081)
- Trello board: [The Trello Board](https://trello.com/invite/b/6a9acac8c426fce02848749d/ATTI69aed775d344ef2fae688f4cdcccac6a69035B78/my-trello-board).

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

![System Architecture](docs/architecture-diagram.png)

The application transforms unstructured MTN MoMo SMS notifications into structured database entries to expose financial patterns[cite: 1]:

1. **Move 1: Read (`data/raw/`):** Reads raw SMS text nodes from `momo.xml`[cite: 1].
2. **Move 2: Extract & Transform (`etl/`):**
   - **Parsing (`parse_xml.py`):** Loops over messages to extract sender metadata, timestamps, and message bodies[cite: 1].
   - **Clean & Normalize (`clean_normalize.py`):** Extracts currency amounts (e.g., `"2,000 RWF"` to `2000`), normalizes timestamps, and unifies telephone formats[cite: 1].
   - **Categorize (`categorize.py`):** Uses regex matching against text patterns to tag transfers, merchant pay, airtime, and cash-in/out[cite: 1].
   - **Dead-Letter Handling:** Routes corrupted, unexpected, or promotional junk to `data/logs/dead_letter/` to prevent crashes[cite: 1].
3. **Move 3: Store (`data/`):** Writes clean records into SQLite (`data/db.sqlite3`) so analytical summaries can be computed without re-reading the XML[cite: 1].
4. **Move 4: Display (`web/`):** Aggregates insights into `data/processed/dashboard.json`, feeding the interactive web interface (`index.html` and `chart_handler.js`) to render charts and transaction metrics[cite: 1].

## Database Design

The MoMo SMS system uses a relational database with six main entities:

- `users` – stores user information.
- `sms_messages` – stores imported SMS data.
- `transaction_categories` – stores transaction categories.
- `transactions` – stores financial transactions.
- `transaction_participants` – links users to transactions.
- `system_logs` – records system events.

### JSON Data Modeling

JSON examples are available in `examples/json_schemas.json`.

The JSON models show how related SQL records can be nested into API responses. For example, a transaction can include its category and participants with their user information.

### Project Files

- ERD: `docs/erd_diagram.png`
- Database setup: `database/database_setup.sql`
- JSON models: `examples/json_schemas.json`
- CRUD tests: `database/crud_tests.sql`

### SQL-to-JSON Mapping

The MoMo database stores information in normalized relational tables to reduce duplication and maintain referential integrity. When the data is exposed through an API, related SQL rows can be combined into nested JSON objects. A transaction row provides fields such as amount, fee, currency, balance and transaction date. The category_id foreign key is resolved using the transaction_categories table and represented as a nested category object. Users participating in a transaction are connected through the transaction_participants junction table and are represented as an array of participant objects containing each user's role and information. The related SMS record can also be nested as source_sms.

SQL INT, BIGINT and DECIMAL values are represented as JSON numbers. SQL VARCHAR, CHAR, TEXT and DATETIME values are represented as JSON strings, while SQL NULL becomes JSON null. One-to-many and many-to-many relationships are represented using JSON arrays. This structure allows the normalized relational database to remain efficient while presenting convenient, readable API responses to client applications.

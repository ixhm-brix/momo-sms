"""In-memory transaction store.

Holds the transactions the API serves. `load()` fills the list from the JSON
file produced by the XML parser; the server calls it once at startup.

Team contract: every record is a dict with an integer "id" field.
"""

import json
import os
import sys

# Default to <repo root>/data/transactions.json so the path does not depend on
# the directory the server was started from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(_REPO_ROOT, "data", "transactions.json")

# The one list every module shares. `load()` fills it in place, so
# `from api.store import transactions` keeps working after a reload.
transactions = []


def load(path=DEFAULT_PATH):
    """Load transactions from `path` into `transactions` and return the list.

    Accepts either a bare JSON array or an object with a "transactions" key.
    A missing file leaves the list empty and warns, so the API still starts
    before the parser has produced its output.
    """
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        print(f"store: {path} not found, starting with no transactions",
              file=sys.stderr)
        data = []

    if isinstance(data, dict):
        data = data.get("transactions", [])

    transactions.clear()
    transactions.extend(data)
    return transactions


def next_id():
    """Return the next free integer id (1 when there are no transactions)."""
    ids = [record["id"] for record in transactions
           if isinstance(record.get("id"), int)]
    return max(ids) + 1 if ids else 1

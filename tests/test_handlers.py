"""
Unit Tests for api/handlers.py - no server needed.

HOW TO RUN (from the project's main folder, the one that contains api/ and data/):
    python -m tests.test_handlers

Each check prints PASS or FAIL. The tests only change the data in memory;
data/transactions.json on disk is never modified.
"""

import os

from api import store
from api.handlers import create_transaction, update_transaction, delete_transaction

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_FOLDER, "data", "transactions.json")

passed = 0
failed = 0


def check(description, condition):
    """Print PASS or FAIL for one check and count the result."""
    global passed, failed
    if condition:
        passed = passed + 1
        print(f"  PASS  {description}")
    else:
        failed = failed + 1
        print(f"  FAIL  {description}")


def is_error(result, status_code):
    """True if `result` is an error in the team format with this status code."""
    payload, code = result
    return code == status_code and list(payload.keys()) == ["error"]


# A valid body we can reuse in several tests.
VALID_BODY = {
    "transaction_type": "payment",
    "amount": 5000,
    "sender": "Account Owner",
    "receiver": "Alice Uwase",
    "timestamp": "2025-01-15 10:30:00",
}


def test_create():
    print("\nPOST - create_transaction")
    count_before = len(store.transactions)
    expected_id = store.next_id()

    payload, code = create_transaction(VALID_BODY)
    check("valid body returns 201", code == 201)
    check("new record gets the next id", payload["id"] == expected_id)
    check("new record is added to store.transactions",
          len(store.transactions) == count_before + 1)
    check("new record has the same fields as a parsed record",
          set(payload.keys()) == set(store.transactions[0].keys()))
    check("missing optional fields get defaults",
          payload["status"] == "completed" and payload["currency"] == "RWF"
          and payload["fee"] is None)

    count_before = len(store.transactions)
    check("missing required field -> 400",
          is_error(create_transaction({"amount": 5000}), 400))
    check("unknown field -> 400",
          is_error(create_transaction({**VALID_BODY, "colour": "red"}), 400))
    check("sending an id -> 400",
          is_error(create_transaction({**VALID_BODY, "id": 5}), 400))
    check("amount as text -> 400",
          is_error(create_transaction({**VALID_BODY, "amount": "5000"}), 400))
    check("amount True/False -> 400",
          is_error(create_transaction({**VALID_BODY, "amount": True}), 400))
    check("negative amount -> 400",
          is_error(create_transaction({**VALID_BODY, "amount": -10}), 400))
    check("empty sender -> 400",
          is_error(create_transaction({**VALID_BODY, "sender": "   "}), 400))
    check("sender null -> 400",
          is_error(create_transaction({**VALID_BODY, "sender": None}), 400))
    check("unknown transaction_type -> 400",
          is_error(create_transaction({**VALID_BODY, "transaction_type": "gift"}), 400))
    check("unknown status -> 400",
          is_error(create_transaction({**VALID_BODY, "status": "done"}), 400))
    check("empty body -> 400", is_error(create_transaction({}), 400))
    check("body that is not a dict -> 400", is_error(create_transaction([1, 2]), 400))
    check("failed requests did not add anything",
          len(store.transactions) == count_before)

    payload, code = create_transaction({**VALID_BODY, "fee": None})
    check("fee null is allowed -> 201", code == 201)

    return payload["id"]


def test_update(tid):
    print("\nPUT - update_transaction")
    payload, code = update_transaction(tid, {"amount": 7500, "status": "failed"})
    check("valid update returns 200", code == 200)
    check("sent fields are changed", payload["amount"] == 7500 and payload["status"] == "failed")
    check("other fields are unchanged", payload["receiver"] == "Alice Uwase")
    check("change is saved in store.transactions",
          any(t["id"] == tid and t["amount"] == 7500 for t in store.transactions))

    check("unknown id -> 404", is_error(update_transaction(999999, {"amount": 1}), 404))
    check("changing the id -> 400", is_error(update_transaction(tid, {"id": 1}), 400))
    check("invalid amount -> 400", is_error(update_transaction(tid, {"amount": 0}), 400))

    update_transaction(tid, {"receiver": "Bob", "amount": "wrong"})
    stored = [t for t in store.transactions if t["id"] == tid][0]
    check("a rejected update changes nothing (not even valid fields)",
          stored["receiver"] == "Alice Uwase")

    payload, code = update_transaction(1, {"receiver": "Jane S."})
    check("can update an original parsed record", code == 200 and payload["id"] == 1)


def test_delete(tid):
    print("\nDELETE - delete_transaction")
    count_before = len(store.transactions)

    payload, code = delete_transaction(tid)
    check("delete returns 200 and the agreed message",
          code == 200 and payload == {"message": "deleted"})
    check("record is removed from store.transactions",
          len(store.transactions) == count_before - 1
          and all(t["id"] != tid for t in store.transactions))
    check("deleting the same id again -> 404", is_error(delete_transaction(tid), 404))
    check("unknown id -> 404", is_error(delete_transaction(999999), 404))


if __name__ == "__main__":
    store.load(DATA_FILE)
    print(f"Loaded {len(store.transactions)} transactions from {DATA_FILE}")

    new_id = test_create()
    test_update(new_id)
    test_delete(new_id)

    print(f"\nResult: {passed} passed, {failed} failed")

"""
MoMo Transactions API - POST, PUT and DELETE logic
---------------------------------------------------

WHAT THIS FILE DOES
    Creates, updates and deletes transactions in the shared list
    store.transactions. It contains exactly three public functions:

        create_transaction(body)          -> used for POST   /transactions
        update_transaction(tid, body)     -> used for PUT    /transactions/{id}
        delete_transaction(tid)           -> used for DELETE /transactions/{id}

WHAT EVERY FUNCTION RETURNS
    A pair: (payload, status_code)
        created           -> (new_record, 201)
        updated           -> (updated_record, 200)
        deleted           -> ({"message": "deleted"}, 200)
        id not found      -> ({"error": "transaction not found"}, 404)
        bad/missing data  -> ({"error": "<what is wrong>"}, 400)

HOW TO ADD OR CHANGE A FIELD
    1. Add the field and its type to FIELD_TYPES below.
    2. If it must always be sent on create, add it to REQUIRED_FIELDS.
    3. If it is allowed to be null, add it to NULLABLE_FIELDS.
    4. Run the tests: python -m tests.test_handlers
"""

from api import store


# Rules that describe a valid transaction
# (these match the records the parser writes to data/transactions.json)

NUMBER = (int, float)   # "any number" means an int or a float

# Every field a client may send, and the type its value must have.
# "id" is not here on purpose: only the server/store decides ids.
FIELD_TYPES = {
    "transaction_type": str,
    "status": str,
    "amount": NUMBER,
    "currency": str,
    "sender": str,
    "receiver": str,
    "timestamp": str,
    "fee": NUMBER,
    "new_balance": NUMBER,
    "transaction_ref": str,
    "sms_date_ms": str,
    "readable_date": str,
    "body": str,
}

# Fields that must be sent when creating a new transaction (POST).
REQUIRED_FIELDS = ["transaction_type", "amount", "sender", "receiver"]

# Fields that are allowed to be null. In the parsed data these are
# null when the SMS did not mention them (for example, no fee,no timestamp).
NULLABLE_FIELDS = [
    "timestamp", "fee", "new_balance", "transaction_ref",
    "sms_date_ms", "readable_date", "body",
]

# Values used for fields the client did not send when creating.
# Any field not listed here defaults to None.
DEFAULT_VALUES = {
    "status": "completed",
    "currency": "RWF",
}

# The transaction types the parser produces.
ALLOWED_TRANSACTION_TYPES = [
    "incoming_money", "payment", "transfer", "bank_deposit", "bank_transfer",
    "withdrawal", "airtime", "cash_power", "bundle_purchase", "direct_debit",
    "reversal", "failed_payment", "otp_notification", "other",
]

ALLOWED_STATUSES = ["completed", "failed", "reversed", "info"]


# Helper functions (used by the three public functions below)

def error(message, status_code):
    """Build an error result in the team format: ({"error": ...}, code)."""
    return {"error": message}, status_code


def find_index(tid):
    """
    Return the position of the transaction with id `tid` in
    store.transactions, or None if there is no such transaction.
    """
    for index, transaction in enumerate(store.transactions):
        if transaction["id"] == tid:
            return index
    return None


def describe_type(expected_type):
    """Turn a Python type into words for error messages."""
    if expected_type == NUMBER:
        return "a number"
    return "text"


def check_one_field(field, value):
    """
    Check a single field's value.
    Returns an error message (text), or None if the value is fine.
    """
    # null is only allowed for some fields
    if value is None:
        if field in NULLABLE_FIELDS:
            return None
        return f"'{field}' cannot be null"

    # In Python, True/False count as numbers (True == 1), so reject them first
    expected_type = FIELD_TYPES[field]
    if isinstance(value, bool) or not isinstance(value, expected_type):
        return f"'{field}' must be {describe_type(expected_type)}"

    # Text must not be empty or only spaces
    if isinstance(value, str) and value.strip() == "":
        return f"'{field}' cannot be empty"

    # Rules for specific fields
    if field == "amount" and value <= 0:
        return "'amount' must be greater than 0"
    if field in ("fee", "new_balance") and value < 0:
        return f"'{field}' cannot be negative"
    if field == "transaction_type" and value not in ALLOWED_TRANSACTION_TYPES:
        return f"'transaction_type' must be one of: {', '.join(ALLOWED_TRANSACTION_TYPES)}"
    if field == "status" and value not in ALLOWED_STATUSES:
        return f"'status' must be one of: {', '.join(ALLOWED_STATUSES)}"

    return None


def check_body(body, is_update):
    """
    Check the whole request body.
    is_update=False (POST): required fields must be present.
    is_update=True  (PUT):  only the fields that were sent are checked.
    Returns an error message (text), or None if the body is valid.
    """
    if not isinstance(body, dict):
        return "request body must be a JSON object"

    if len(body) == 0:
        return "request body is empty"

    if "id" in body:
        return "'id' is set by the server and cannot be sent"

    unknown_fields = [field for field in body if field not in FIELD_TYPES]
    if unknown_fields:
        return f"unknown field(s): {', '.join(unknown_fields)}"

    if not is_update:
        missing_fields = [field for field in REQUIRED_FIELDS if field not in body]
        if missing_fields:
            return f"missing required field(s): {', '.join(missing_fields)}"

    for field, value in body.items():
        message = check_one_field(field, value)
        if message is not None:
            return message

    return None


# Public functions (used by the server)

def create_transaction(body):

    #POST /transactions - add a new transaction.

    message = check_body(body, is_update=False)
    if message is not None:
        return error(message, 400)

    # Build the new record with EVERY field, in the same order as the parsed
    # records, so all transactions have the same shape.
    new_transaction = {"id": store.next_id()}
    for field in FIELD_TYPES:
        if field in body:
            new_transaction[field] = body[field]
        else:
            new_transaction[field] = DEFAULT_VALUES.get(field)

    store.transactions.append(new_transaction)

    # Return a copy, so whoever receives it cannot change the stored record
    return dict(new_transaction), 201


def update_transaction(tid, body):
    """
    PUT /transactions/{id} - change some fields of an existing transaction.
    Only the fields in `body` change; all other fields keep their values."""
    index = find_index(tid)
    if index is None:
        return error("transaction not found", 404)

    # Check everything BEFORE changing anything, so a bad request
    # never leaves a record half-updated.
    message = check_body(body, is_update=True)
    if message is not None:
        return error(message, 400)

    transaction = store.transactions[index]
    transaction.update(body)

    return dict(transaction), 200


def delete_transaction(tid):
    """
    DELETE /transactions/{id} - remove a transaction.

    Example:
        delete_transaction(1692) -> ({"message": "deleted"}, 200)
    """
    index = find_index(tid)
    if index is None:
        return error("transaction not found", 404)

    # .pop() removes the item from the shared list itself (no new list)
    store.transactions.pop(index)

    return {"message": "deleted"}, 200

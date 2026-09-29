# MoMo SMS Transactions API

REST API for MTN MoMo SMS transactions, built with Python's `http.server`.

| | |
|---|---|
| Base URL | `http://127.0.0.1:8000` |
| Format | JSON |
| Auth | HTTP Basic Auth: `admin` / `momo123` (override with `API_USERNAME`, `API_PASSWORD`) |
| Run | `python -m api.server` (from the repository root) |

Data is loaded from `data/transactions.json` at startup. Changes are kept in memory only and are lost on restart.

## Authentication

Every request needs a Basic Auth header (`curl -u admin:momo123`, or **Authorization → Basic Auth** in Postman). Missing or wrong credentials return:

```
401 Unauthorized
{"error": "Unauthorized", "status_code": 401, "message": "Invalid or missing Basic Authentication credentials."}
```

## Transaction fields

| Field | Type | Notes |
|---|---|---|
| `id` | integer | Set by the server, read-only |
| `transaction_type` | string | `incoming_money`, `payment`, `transfer`, `bank_deposit`, `bank_transfer`, `withdrawal`, `airtime`, `cash_power`, `bundle_purchase`, `direct_debit`, `reversal`, `failed_payment`, `otp_notification`, `other` |
| `status` | string | `completed` (default), `failed`, `reversed`, `info` |
| `amount` | number | Greater than 0 |
| `currency` | string | Default `RWF` |
| `sender`, `receiver` | string | Non-empty |
| `fee`, `new_balance` | number \| null | 0 or more |
| `timestamp`, `transaction_ref`, `sms_date_ms`, `readable_date`, `body` | string \| null | |

---

## GET /transactions

List all transactions.

```bash
curl -u admin:momo123 http://127.0.0.1:8000/transactions
```

**200 OK:** an array of every transaction:

```json
[
  {"id": 1, "transaction_type": "incoming_money", "amount": 2000, "sender": "Jane Smith", "...": "..."},
  {"id": 2, "transaction_type": "payment", "amount": 1000, "...": "..."}
]
```

**Errors:** 401

## GET /transactions/{id}

Get one transaction.

```bash
curl -u admin:momo123 http://127.0.0.1:8000/transactions/1
```

**200 OK**

```json
{
  "id": 1,
  "transaction_type": "incoming_money",
  "status": "completed",
  "amount": 2000,
  "currency": "RWF",
  "sender": "Jane Smith",
  "receiver": "Account Owner",
  "timestamp": "2024-05-10 16:30:51",
  "fee": null,
  "new_balance": 2000,
  "transaction_ref": "76662021700",
  "sms_date_ms": "1715351458724",
  "readable_date": "10 May 2024 4:30:58 PM",
  "body": "You have received 2000 RWF from Jane Smith (*********013) ..."
}
```

**Errors**

| Code | Body |
|---|---|
| 400 | `{"error": "id must be an integer"}` |
| 401 | See Authentication |
| 404 | `{"error": "transaction not found"}` |

## POST /transactions

Create a transaction. Required: `transaction_type`, `amount`, `sender`, `receiver`. Other fields are optional; missing ones are stored as `null` or their default. `id` must not be sent.

```bash
curl -u admin:momo123 -X POST http://127.0.0.1:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"transaction_type": "payment", "amount": 5000, "sender": "Account Owner", "receiver": "Alice Uwase"}'
```

**201 Created**

```json
{
  "id": 1692,
  "transaction_type": "payment",
  "status": "completed",
  "amount": 5000,
  "currency": "RWF",
  "sender": "Account Owner",
  "receiver": "Alice Uwase",
  "timestamp": null,
  "fee": null,
  "new_balance": null,
  "transaction_ref": null,
  "sms_date_ms": null,
  "readable_date": null,
  "body": null
}
```

**Errors**

| Code | Example body |
|---|---|
| 400 | `{"error": "invalid JSON"}` |
| 400 | `{"error": "missing required field(s): sender, receiver"}` |
| 400 | `{"error": "'amount' must be greater than 0"}` |
| 400 | `{"error": "'id' is set by the server and cannot be sent"}` |
| 400 | `{"error": "unknown field(s): colour"}` |
| 401 | See Authentication |

## PUT /transactions/{id}

Update a transaction. Only the fields sent are changed, using the same rules as POST. If any field is invalid, nothing changes.

```bash
curl -u admin:momo123 -X PUT http://127.0.0.1:8000/transactions/1692 \
  -H "Content-Type: application/json" \
  -d '{"amount": 7500, "status": "failed"}'
```

**200 OK:** the full updated record:

```json
{"id": 1692, "transaction_type": "payment", "status": "failed", "amount": 7500, "...": "..."}
```

**Errors**

| Code | Example body |
|---|---|
| 400 | `{"error": "id must be an integer"}` |
| 400 | `{"error": "'status' must be one of: completed, failed, reversed, info"}` |
| 401 | See Authentication |
| 404 | `{"error": "transaction not found"}` |

## DELETE /transactions/{id}

Delete a transaction.

```bash
curl -u admin:momo123 -X DELETE http://127.0.0.1:8000/transactions/1692
```

**200 OK**

```json
{"message": "deleted"}
```

**Errors**

| Code | Body |
|---|---|
| 400 | `{"error": "id must be an integer"}` |
| 401 | See Authentication |
| 404 | `{"error": "transaction not found"}` |

---

## Status codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Transaction created |
| 400 | Invalid id, JSON or field value |
| 401 | Missing or wrong credentials |
| 404 | Transaction or path not found |

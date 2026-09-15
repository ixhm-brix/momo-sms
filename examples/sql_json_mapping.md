# SQL to JSON Mapping

The relational database tables are serialized into JSON objects for API responses.

| SQL Table | JSON Representation | Relationship |
|---|---|---|
| users | `participants[].user` | User information is nested inside each participant |
| transaction_categories | `category` | Transaction category is nested inside the transaction |
| sms_messages | `sms` | Original SMS information is nested inside the transaction |
| transactions | Root transaction object | Contains the main transaction information |
| transaction_participants | `participants[]` | Many-to-many relationship is represented as an array |
| system_logs | `logs[]` or separate log response | Stores processing and system events |

## Example

The SQL `transactions` table provides the main transaction fields:

- `transaction_id`
- `external_txn_id`
- `amount`
- `fee`
- `balance_after`
- `status`
- `transaction_date`

The `transaction_categories` table is represented by the nested `category` object.

The `transaction_participants` table is represented by the `participants` array, with each participant containing a role and related user information.

The `users` table is represented by the nested `user` object inside each participant.

The `sms_messages` table is represented by the nested `sms` object, which keeps the original SMS information for traceability.

This structure allows the relational database to be returned as a structured API response while preserving the relationships between transactions, users, categories, and original SMS messages.

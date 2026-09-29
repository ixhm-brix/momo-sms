"""REST API for MoMo SMS transactions, built on http.server.

Run from the repository root:

    python -m api.server

Routes:
    GET    /transactions        list every transaction
    GET    /transactions/{id}   one transaction
    POST   /transactions        create, delegated to api.handlers
    PUT    /transactions/{id}   update, delegated to api.handlers
    DELETE /transactions/{id}   delete, delegated to api.handlers

The GET endpoints are implemented here. The write verbs only parse the
request and hand off to api.handlers. Basic Auth lives in api.auth and is
wired in separately.
"""

import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from api import handlers, store

HOST = "127.0.0.1"
PORT = 8000

COLLECTION_PATH = "/transactions"
ITEM_PATTERN = re.compile(r"^/transactions/([^/]+)$")


class TransactionHandler(BaseHTTPRequestHandler):
    """Serves the /transactions routes. One instance per request."""

    server_version = "MoMoAPI/1.0"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def send_json(self, payload, status=200):
        """Send `payload` as a JSON response with the given status code."""
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        """Return the request body as a dict, or None if it is not one.

        None covers both malformed JSON and valid JSON that is not an
        object (a list or a bare string), since the handlers expect a dict.
        The caller turns None into {"error": "invalid JSON"}, 400.
        """
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None

        raw = self.rfile.read(length) if length > 0 else b""
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            return None

        return body if isinstance(body, dict) else None

    def path_only(self):
        """The request path without any query string or trailing slash."""
        path = self.path.split("?", 1)[0]
        return path.rstrip("/") or "/"

    def item_id(self):
        """Return the int id from /transactions/{id}.

        Returns None and sends the error response itself when the path is
        not an item route (404) or the id is not a number (400), so the
        caller just returns without calling into api.handlers.
        """
        match = ITEM_PATTERN.match(self.path_only())
        if match is None:
            self.send_json({"error": "not found"}, 404)
            return None
        try:
            return int(match.group(1))
        except ValueError:
            self.send_json({"error": "id must be an integer"}, 400)
            return None

    # ------------------------------------------------------------------
    # read endpoints, implemented here
    # ------------------------------------------------------------------
    def do_GET(self):
        path = self.path_only()

        if path == COLLECTION_PATH:
            self.send_json(store.transactions)
            return

        transaction_id = self.item_id()
        if transaction_id is None:
            return

        for transaction in store.transactions:
            if transaction.get("id") == transaction_id:
                self.send_json(transaction)
                return

        self.send_json({"error": "transaction not found"}, 404)

    # ------------------------------------------------------------------
    # write endpoints, delegated to api.handlers
    # ------------------------------------------------------------------
    def do_POST(self):
        if self.path_only() != COLLECTION_PATH:
            self.send_json({"error": "not found"}, 404)
            return

        body = self.read_body()
        if body is None:
            self.send_json({"error": "invalid JSON"}, 400)
            return

        payload, status = handlers.create_transaction(body)
        self.send_json(payload, status)

    def do_PUT(self):
        transaction_id = self.item_id()
        if transaction_id is None:
            return

        body = self.read_body()
        if body is None:
            self.send_json({"error": "invalid JSON"}, 400)
            return

        payload, status = handlers.update_transaction(transaction_id, body)
        self.send_json(payload, status)

    def do_DELETE(self):
        transaction_id = self.item_id()
        if transaction_id is None:
            return

        payload, status = handlers.delete_transaction(transaction_id)
        self.send_json(payload, status)


def main():
    store.load()
    print(f"{len(store.transactions)} transactions loaded")

    server = HTTPServer((HOST, PORT), TransactionHandler)
    print(f"Serving on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

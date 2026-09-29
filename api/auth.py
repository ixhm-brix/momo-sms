"""
Authentication module for MoMo SMS REST API.
Handles HTTP Basic Authentication header parsing, credential validation,
and HTTP 401 Unauthorized response generation.
"""

import base64
import json
import os

VALID_USERNAME = os.environ.get("API_USERNAME", "admin")
VALID_PASSWORD = os.environ.get("API_PASSWORD", "momo123")


def parse_basic_auth_header(auth_header: str):
    """
    Parses the HTTP Authorization header: 'Basic <base64_encoded_str>'
    Returns (username, password) or (None, None).
    """
    if not auth_header or not auth_header.startswith("Basic "):
        return None, None

    try:
        encoded_credentials = auth_header.split(" ", 1)[1].strip()
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_str = decoded_bytes.decode("utf-8")

        if ":" not in decoded_str:
            return None, None

        username, password = decoded_str.split(":", 1)
        return username, password
    except Exception:
        return None, None


def authenticate_credentials(username: str, password: str) -> bool:
    """Verifies credentials match configured values."""
    return username == VALID_USERNAME and password == VALID_PASSWORD


def check_request_auth(headers) -> bool:
    """Inspects Authorization header from BaseHTTPRequestHandler."""
    auth_header = headers.get("Authorization")
    username, password = parse_basic_auth_header(auth_header)
    if not username or not password:
        return False
    return authenticate_credentials(username, password)


def send_401_unauthorized(handler, realm="MoMo SMS API"):
    """Sends HTTP 401 Unauthorized with WWW-Authenticate header."""
    handler.send_response(401)
    handler.send_header("WWW-Authenticate", f'Basic realm="{realm}"')
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()

    error_response = {
        "error": "Unauthorized",
        "status_code": 401,
        "message": "Invalid or missing Basic Authentication credentials."
    }
    handler.wfile.write(json.dumps(error_response).encode("utf-8"))

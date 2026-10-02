"""Lightweight HTTP Server and REST API for Career Preferences & Opportunity Auditing.

Provides a zero-external-dependency web server built on Python standard library
`http.server.ThreadingHTTPServer` and `SimpleHTTPRequestHandler`. Serves the
Preference Manager static web UI and exposes REST API endpoints for:
- GET  /api/preferences : Fetch current preferences JSON with CORS
- POST /api/save        : Update preferences JSON and sync to Obsidian Markdown
- POST /api/audit       : Execute opportunity audit and generate markdown report
"""

import argparse
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
import threading
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional, Tuple, Union

try:
    from http.server import ThreadingHTTPServer
except ImportError:
    ThreadingHTTPServer = HTTPServer  # type: ignore

# Ensure the local script directory is in sys.path for direct script execution
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from preference_models import (
    DEFAULT_PREFERENCES,
    load_preferences_json,
    save_preferences_json,
    sync_to_markdown,
)
from audit_preferences import (
    audit_opportunities_against_preferences,
    generate_markdown_audit_report,
)

# Canonical project file paths
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
DEFAULT_PREFERENCES_JSON = os.path.join(
    PROJECT_ROOT, "001-background", "preferences.json"
)
DEFAULT_PREFERENCES_MD = os.path.join(
    PROJECT_ROOT, "001-background", "preferences.md"
)
DEFAULT_OPPORTUNITIES_JSON = os.path.join(
    PROJECT_ROOT, "004-work-opportunities", "database", "opportunities.json"
)
DEFAULT_AUDIT_MD = os.path.join(
    PROJECT_ROOT, "004-work-opportunities", "opportunities-preference-audit.md"
)
DEFAULT_WEB_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "web")
)


class PreferenceRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler serving static web assets and REST API endpoints."""

    def __init__(self, *args: Any, directory: Optional[str] = None, **kwargs: Any) -> None:
        if directory is None and len(args) >= 3 and hasattr(args[2], "web_directory"):
            directory = getattr(args[2], "web_directory", DEFAULT_WEB_DIR)
        elif directory is None:
            directory = DEFAULT_WEB_DIR
        super().__init__(*args, directory=directory, **kwargs)

    def _send_cors_headers(self) -> None:
        """Attach CORS headers to support cross-origin API interactions."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json_response(self, status_code: int, data: Any) -> None:
        """Serialize and transmit JSON response with appropriate headers."""
        body_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_OPTIONS(self) -> None:
        """Handle HTTP OPTIONS preflight requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests for REST API endpoints and static assets."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        if not path:
            path = "/"

        if path == "/api/preferences":
            pref_path = getattr(self.server, "preferences_path", DEFAULT_PREFERENCES_JSON)
            try:
                pref_data = load_preferences_json(pref_path)
                self._send_json_response(200, pref_data)
            except Exception as e:
                self._send_json_response(500, {"success": False, "error": f"Error loading preferences: {str(e)}"})
        elif path.startswith("/api/"):
            self._send_json_response(404, {"success": False, "error": f"API endpoint '{parsed_url.path}' not found"})
        else:
            # Delegate to SimpleHTTPRequestHandler for static web files
            super().do_GET()

    def do_POST(self) -> None:
        """Handle POST requests for REST API endpoints."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")

        if path == "/api/save":
            self._handle_save()
        elif path == "/api/audit":
            self._handle_audit()
        elif path.startswith("/api/"):
            self._send_json_response(404, {"success": False, "error": f"API endpoint '{parsed_url.path}' not found"})
        else:
            self._send_json_response(404, {"success": False, "error": "Not Found"})

    def _handle_save(self) -> None:
        """Handle POST /api/save request."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_length = 0

        if content_length <= 0:
            self._send_json_response(400, {"success": False, "error": "Missing or empty request body"})
            return

        try:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw_body)
        except Exception as e:
            self._send_json_response(400, {"success": False, "error": f"Invalid JSON payload: {str(e)}"})
            return

        if not isinstance(payload, dict):
            self._send_json_response(400, {"success": False, "error": "Payload must be a JSON dictionary"})
            return

        pref_path = getattr(self.server, "preferences_path", DEFAULT_PREFERENCES_JSON)
        md_path = getattr(self.server, "markdown_path", DEFAULT_PREFERENCES_MD)

        today = datetime.now().strftime("%Y-%m-%d")
        payload["updated"] = today
        if "metadata" in payload and isinstance(payload["metadata"], dict):
            payload["metadata"]["updated"] = today

        try:
            save_preferences_json(payload, pref_path)
            sync_to_markdown(payload, md_path)
            self._send_json_response(200, {
                "success": True,
                "message": "Preferences saved and synchronized to Markdown successfully",
                "preferences_path": pref_path,
                "markdown_path": md_path,
            })
        except Exception as e:
            self._send_json_response(500, {"success": False, "error": f"Error saving preferences: {str(e)}"})

    def _handle_audit(self) -> None:
        """Handle POST /api/audit request."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            content_length = 0

        pref_data = None
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                req_json = json.loads(raw_body)
                if isinstance(req_json, dict) and ("candidate" in req_json or "preferences" in req_json):
                    pref_data = req_json.get("preferences", req_json)
            except Exception:
                pref_data = None

        pref_path = getattr(self.server, "preferences_path", DEFAULT_PREFERENCES_JSON)
        opps_path = getattr(self.server, "opportunities_path", DEFAULT_OPPORTUNITIES_JSON)
        audit_md_path = getattr(self.server, "audit_report_path", DEFAULT_AUDIT_MD)

        if pref_data is None:
            try:
                pref_data = load_preferences_json(pref_path)
            except Exception as e:
                self._send_json_response(500, {"success": False, "error": f"Error loading preferences: {str(e)}"})
                return

        if os.path.exists(opps_path):
            try:
                with open(opps_path, "r", encoding="utf-8") as f:
                    opp_data = json.load(f)
            except Exception:
                opp_data = {"opportunities": []}
        else:
            opp_data = {"opportunities": []}

        try:
            audit_result = audit_opportunities_against_preferences(pref_data, opp_data)
            report_file = generate_markdown_audit_report(audit_result, output_path=audit_md_path)
            self._send_json_response(200, {
                "success": True,
                "audit": audit_result,
                "report_path": report_file,
            })
        except Exception as e:
            self._send_json_response(500, {"success": False, "error": f"Error running audit: {str(e)}"})


def create_server(
    port: int = 8765,
    host: str = "127.0.0.1",
    preferences_path: Optional[str] = None,
    markdown_path: Optional[str] = None,
    opportunities_path: Optional[str] = None,
    audit_report_path: Optional[str] = None,
    directory: Optional[str] = None,
    max_retries: int = 0,
) -> Tuple[ThreadingHTTPServer, threading.Thread]:
    """Create and start a ThreadingHTTPServer in a background daemon thread.

    Args:
        port: Desired port (default 8765). If 0, system selects an ephemeral port.
        host: Host binding address (default '127.0.0.1').
        preferences_path: Path to preferences JSON.
        markdown_path: Path to output synchronized preferences Markdown.
        opportunities_path: Path to opportunities database JSON.
        audit_report_path: Path to output audit Markdown report.
        directory: Directory for static web assets.
        max_retries: Number of port retries if port is busy.

    Returns:
        Tuple of (ThreadingHTTPServer instance, background running Thread).
    """
    web_dir = directory or DEFAULT_WEB_DIR
    if not os.path.exists(web_dir):
        os.makedirs(web_dir, exist_ok=True)
    index_file = os.path.join(web_dir, "index.html")
    if not os.path.exists(index_file):
        with open(index_file, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Preference Manager</h1></body></html>\n")

    server = None
    last_error = None
    attempts = max(1, max_retries + 1) if port != 0 else 1

    for attempt in range(attempts):
        current_port = port + attempt if port != 0 else 0
        try:
            server = ThreadingHTTPServer((host, current_port), PreferenceRequestHandler)
            break
        except OSError as e:
            last_error = e
            if attempt == attempts - 1:
                raise e

    if server is None:
        raise last_error or RuntimeError(f"Could not bind server to {host}:{port}")

    server.preferences_path = preferences_path or DEFAULT_PREFERENCES_JSON
    server.markdown_path = markdown_path or DEFAULT_PREFERENCES_MD
    server.opportunities_path = opportunities_path or DEFAULT_OPPORTUNITIES_JSON
    server.audit_report_path = audit_report_path or DEFAULT_AUDIT_MD
    server.web_directory = web_dir

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def main() -> None:
    """CLI entrypoint supporting --port, --host, and --open."""
    parser = argparse.ArgumentParser(description="Diego Perea León — Preference Web Server & API")
    parser.add_argument("--port", "-p", type=int, default=8765, help="Port to run server on (default: 8765)")
    parser.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    parser.add_argument("--open", "-o", action="store_true", help="Automatically open web browser UI")
    args = parser.parse_args()

    server, thread = create_server(port=args.port, host=args.host, max_retries=10)
    actual_port = server.server_address[1]
    url = f"http://{args.host}:{actual_port}/"

    print("=" * 60)
    print("PREFERENCE MANAGER WEB SERVER")
    print("=" * 60)
    print(f"Server URL:     {url}")
    print(f"API Endpoints:  {url}api/preferences")
    print(f"                {url}api/save")
    print(f"                {url}api/audit")
    print(f"Web Root:       {getattr(server, 'web_directory', DEFAULT_WEB_DIR)}")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    if args.open:
        webbrowser.open(url)

    try:
        while thread.is_alive():
            thread.join(timeout=1.0)
    except KeyboardInterrupt:
        print("\nGracefully shutting down server...")
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
        print("Server shutdown complete.")


if __name__ == "__main__":
    main()

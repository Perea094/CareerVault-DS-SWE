"""Unit tests for Preference Web Server and REST API Endpoints.

Tests:
- GET /api/preferences returns 200, JSON content-type, CORS headers, and valid preferences structure.
- POST /api/save saves payload to JSON, synchronizes to Markdown, and returns success.
- POST /api/audit triggers audit against opportunities and returns audit results.
- Static file serving from the web directory (e.g. index.html).
- Graceful port handling and server shutdown.
- Error handling for invalid JSON payload and unknown endpoints.
"""

import http.client
import json
import os
import sys
import tempfile
import threading
import time
import unittest

# Ensure the scripts directory is in sys.path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            ".agents",
            "skills",
            "preference-manager",
            "scripts",
        )
    ),
)

from preference_server import create_server, PreferenceRequestHandler


class TestPreferenceServer(unittest.TestCase):
    def setUp(self):
        """Set up temporary sandbox directory with mock files for each test."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.pref_json_path = os.path.join(self.test_dir.name, "preferences.json")
        self.pref_md_path = os.path.join(self.test_dir.name, "preferences.md")
        self.opps_json_path = os.path.join(self.test_dir.name, "opportunities.json")
        self.audit_md_path = os.path.join(self.test_dir.name, "opportunities-preference-audit.md")
        self.web_dir = os.path.join(self.test_dir.name, "web")
        os.makedirs(self.web_dir, exist_ok=True)

        # Create dummy index.html, style.css, and app.js in web dir
        with open(os.path.join(self.web_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Preference Manager</h1></body></html>")
        with open(os.path.join(self.web_dir, "style.css"), "w", encoding="utf-8") as f:
            f.write("/* CSS */ body { background: #1e1e24; }")
        with open(os.path.join(self.web_dir, "app.js"), "w", encoding="utf-8") as f:
            f.write("// JS\nconsole.log('App loaded');")

        # Initial mock preferences
        self.sample_preferences = {
            "version": "1.1",
            "updated": "2026-10-02",
            "status": "active",
            "candidate": {
                "name": "Diego Perea León",
                "university": "Tecnológico de Monterrey (Campus Querétaro)",
                "degree": "B.S. Data Science & Mathematics",
                "current_semester": "4th semester",
                "expected_graduation": "May 2028",
                "email_contact": "diego.perea@tec.mx",
            },
            "availability_calendar": {
                "target_weekly_hours_min": 20,
                "target_weekly_hours_max": 30,
                "weekly_available_hours": 30.0,
            },
            "location_visa": {
                "current_location": "Querétaro, Mexico",
                "us_work_authorization": "None",
                "preferred_arrangements": ["Remote", "Hybrid (Querétaro / CDMX)"],
            },
            "deal_breakers": {
                "hard_constraints": ["No onsite 5 days/week during academic semester"],
                "automatic_disqualifiers": ["US citizenship or government security clearance required"],
                "toxic_signals": ["Crypto"],
            },
            "industry_domain": {
                "domains_of_interest": ["GenAI/LLMs", "Machine Learning", "Data Science"],
                "industries_to_avoid": ["Crypto / Web3"],
            },
        }
        with open(self.pref_json_path, "w", encoding="utf-8") as f:
            json.dump(self.sample_preferences, f, indent=2)

        # Mock opportunities
        self.sample_opportunities = [
            {
                "id": "opp-01",
                "company": "Salesforce",
                "role": "AI Builder Intern [Mexico]",
                "tier": "Tier 1: Mexico & LATAM",
                "location": "Mexico City (Remote/Hybrid)",
                "hours_per_week": "20-30",
                "status": "eligible",
                "apply_url": "https://example.com/apply1",
            },
            {
                "id": "opp-02",
                "company": "Lockheed Martin",
                "role": "Defense Software Intern",
                "tier": "Tier 3: US Onsite",
                "location": "Fort Worth, TX",
                "hours_per_week": "40",
                "sponsorship_notes": "US Citizenship required",
                "status": "eligible",
                "apply_url": "https://example.com/apply2",
            },
        ]
        with open(self.opps_json_path, "w", encoding="utf-8") as f:
            json.dump({"opportunities": self.sample_opportunities}, f, indent=2)

        # Start server with ephemeral port (0)
        self.server, self.thread = create_server(
            port=0,
            host="127.0.0.1",
            preferences_path=self.pref_json_path,
            markdown_path=self.pref_md_path,
            opportunities_path=self.opps_json_path,
            audit_report_path=self.audit_md_path,
            directory=self.web_dir,
        )
        self.port = self.server.server_address[1]

    def tearDown(self):
        """Shutdown server and clean up temporary directory."""
        if hasattr(self, "server") and self.server:
            self.server.shutdown()
            self.server.server_close()
        if hasattr(self, "thread") and self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.test_dir.cleanup()

    def _http_request(self, method: str, path: str, body: dict = None, headers: dict = None):
        """Helper to execute HTTP requests against the test server."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        req_headers = headers or {}
        req_data = None
        if body is not None:
            req_data = json.dumps(body).encode("utf-8")
            if "Content-Type" not in req_headers:
                req_headers["Content-Type"] = "application/json"
        conn.request(method, path, body=req_data, headers=req_headers)
        response = conn.getresponse()
        resp_body = response.read().decode("utf-8")
        conn.close()
        return response.status, response.getheaders(), resp_body

    def test_get_preferences_returns_200_and_json(self):
        """Test GET /api/preferences returns 200, valid JSON, and candidate data."""
        status, headers, body = self._http_request("GET", "/api/preferences")
        self.assertEqual(status, 200)

        header_dict = dict(headers)
        content_type = header_dict.get("Content-Type", "")
        self.assertIn("application/json", content_type)
        self.assertEqual(header_dict.get("Access-Control-Allow-Origin"), "*")

        data = json.loads(body)
        self.assertIn("candidate", data)
        self.assertEqual(data["candidate"]["name"], "Diego Perea León")
        self.assertIn("availability_calendar", data)
        self.assertEqual(data["availability_calendar"]["target_weekly_hours_max"], 30)

    def test_post_save_saves_payload_and_syncs_markdown(self):
        """Test POST /api/save updates JSON file, syncs to Markdown, and returns success."""
        updated_payload = dict(self.sample_preferences)
        updated_payload["availability_calendar"] = {
            "target_weekly_hours_min": 15,
            "target_weekly_hours_max": 25,
            "weekly_available_hours": 25.0,
        }
        updated_payload["work_arrangement"] = {
            "hours_per_week": "15-25 (part-time)",
            "hours_flexibility": True,
        }
        updated_payload["compensation_benefits"] = {
            "minimum_hourly": 35,
        }

        status, headers, body = self._http_request("POST", "/api/save", body=updated_payload)
        self.assertEqual(status, 200)

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        self.assertIn("message", data)

        # Verify JSON file on disk was updated
        with open(self.pref_json_path, "r", encoding="utf-8") as f:
            saved_json = json.load(f)
        self.assertEqual(saved_json["candidate"]["name"], "Diego Perea León")
        self.assertEqual(saved_json["availability_calendar"]["target_weekly_hours_max"], 25)
        self.assertEqual(saved_json["compensation_benefits"]["minimum_hourly"], 35)

        # Verify Markdown file was synchronized and exists on disk
        self.assertTrue(os.path.exists(self.pref_md_path))
        with open(self.pref_md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        self.assertIn("minimum_hourly: 35", md_content)
        self.assertIn('hours_per_week: "15-25 (part-time)"', md_content)
        self.assertIn("B.S. Data Science & Mathematics", md_content)

    def test_post_audit_triggers_audit_and_returns_result(self):
        """Test POST /api/audit runs audit against opportunities and generates report."""
        status, headers, body = self._http_request("POST", "/api/audit", body={})
        self.assertEqual(status, 200)

        data = json.loads(body)
        self.assertTrue(data.get("success"))
        self.assertIn("audit", data)

        audit_res = data["audit"]
        self.assertIn("summary", audit_res)
        self.assertIn("matches", audit_res)
        self.assertIn("disqualified", audit_res)
        self.assertEqual(audit_res["summary"]["direct_matches"], 1)
        self.assertEqual(audit_res["summary"]["disqualified"], 1)

        # Verify markdown audit report was generated on disk
        self.assertTrue(os.path.exists(self.audit_md_path))
        with open(self.audit_md_path, "r", encoding="utf-8") as f:
            report_content = f.read()
        self.assertIn("Opportunity Audit Report", report_content)
        self.assertIn("Salesforce", report_content)

    def test_options_cors_preflight(self):
        """Test OPTIONS request returns CORS headers."""
        status, headers, _ = self._http_request("OPTIONS", "/api/preferences")
        self.assertIn(status, [200, 204])
        header_dict = dict(headers)
        self.assertEqual(header_dict.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("GET", header_dict.get("Access-Control-Allow-Methods", ""))
        self.assertIn("POST", header_dict.get("Access-Control-Allow-Methods", ""))

    def test_serves_static_files(self):
        """Test server serves static assets from web directory."""
        status, headers, body = self._http_request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Preference Manager", body)

        status, headers, body = self._http_request("GET", "/index.html")
        self.assertEqual(status, 200)
        self.assertIn("Preference Manager", body)

        status, headers, body = self._http_request("GET", "/style.css")
        self.assertEqual(status, 200)
        self.assertIn("#1e1e24", body)

        status, headers, body = self._http_request("GET", "/app.js")
        self.assertEqual(status, 200)
        self.assertIn("App loaded", body)

    def test_serves_real_web_assets(self):
        """Test that default web assets exist and are served properly with HTTP 200."""
        from preference_server import DEFAULT_WEB_DIR
        real_server, real_thread = create_server(port=0, host="127.0.0.1", directory=DEFAULT_WEB_DIR)
        try:
            port = real_server.server_address[1]
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)

            # Check index.html
            conn.request("GET", "/")
            res = conn.getresponse()
            self.assertEqual(res.status, 200)
            index_content = res.read().decode("utf-8")
            self.assertIn("Diego Perea León", index_content)
            self.assertIn("Weekly Availability", index_content)

            # Check style.css
            conn.request("GET", "/style.css")
            res = conn.getresponse()
            self.assertEqual(res.status, 200)
            css_content = res.read().decode("utf-8")
            self.assertIn("--bg-base", css_content)
            self.assertIn("#1e1e24", css_content)

            # Check app.js
            conn.request("GET", "/app.js")
            res = conn.getresponse()
            self.assertEqual(res.status, 200)
            js_content = res.read().decode("utf-8")
            self.assertIn("renderAvailabilityGrid", js_content)
            self.assertIn("loadPreferences", js_content)

            conn.close()
        finally:
            real_server.shutdown()
            real_server.server_close()
            real_thread.join(timeout=2.0)

    def test_not_found_endpoint(self):
        """Test non-existent API endpoint returns 404."""
        status, headers, body = self._http_request("GET", "/api/nonexistent")
        self.assertEqual(status, 404)
        data = json.loads(body)
        self.assertFalse(data.get("success"))

    def test_post_save_invalid_json(self):
        """Test POST /api/save with invalid JSON returns 400."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", "/api/save", body="bad-json-content", headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        resp_body = response.read().decode("utf-8")
        conn.close()

        self.assertEqual(response.status, 400)
        data = json.loads(resp_body)
        self.assertFalse(data.get("success"))

    def test_graceful_shutdown(self):
        """Test creating and gracefully shutting down the server."""
        server, thread = create_server(port=0, host="127.0.0.1", directory=self.web_dir)
        self.assertTrue(thread.is_alive())
        port = server.server_address[1]

        # Verify it can serve a request
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/preferences")
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        conn.close()

        # Graceful shutdown
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)
        self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()

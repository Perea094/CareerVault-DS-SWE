import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime
import os
import sys

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prune_opportunities
from prune_opportunities import check_single_link, is_ats_redirected_to_catalog

class TestPruneOpportunities(unittest.TestCase):
    def test_detect_microsoft_careers_catalog_redirect(self):
        original_url = "https://jobs.careers.microsoft.com/global/en/job/1765432/Software-Engineer-Intern"
        redirected_url = "https://apply.careers.microsoft.com/careers"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Microsoft", reason)

    def test_detect_amazon_jobs_catalog_redirect(self):
        original_url = "https://amazon.jobs/en/jobs/2337339/software-development-engineer-intern"
        redirected_url = "https://amazon.jobs/en/search?base_query="
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Amazon", reason)

    def test_detect_workday_careers_redirect(self):
        original_url = "https://workday.wd5.myworkdayjobs.com/en-US/Workday/job/SWE-Intern_R-12345"
        redirected_url = "https://workday.wd5.myworkdayjobs.com/en-US/Workday/careers"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Workday", reason)

    def test_active_requisition_not_flagged_as_redirect(self):
        original_url = "https://job-boards.greenhouse.io/figma/jobs/6178857004?gh_jid=6178857004"
        final_url = "https://job-boards.greenhouse.io/figma/jobs/6178857004"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, final_url)
        self.assertFalse(is_redirected)

    def test_check_single_link_detects_soft_404_keywords(self):
        opp = {"company": "Acme", "role": "SWE", "apply_url": "https://example.com/job1"}
        mock_resp = MagicMock()
        mock_resp.geturl.return_value = "https://example.com/job1"
        mock_resp.read.return_value = b"<html><body>Search our other open roles. This job is no longer available.</body></html>"
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            _, is_active, reason = check_single_link(opp)
            self.assertFalse(is_active)
            self.assertIn("ATS Closed Message", reason)

    def test_check_single_link_detects_http_404(self):
        opp = {"company": "Acme", "role": "SWE", "apply_url": "https://example.com/job2"}
        import urllib.error
        http_err = urllib.error.HTTPError("https://example.com/job2", 404, "Not Found", {}, None)

        with patch("urllib.request.urlopen", side_effect=http_err):
            _, is_active, reason = check_single_link(opp)
            self.assertFalse(is_active)
            self.assertIn("HTTP 404", reason)

    def test_detect_greenhouse_redirect(self):
        original_url = "https://job-boards.greenhouse.io/stripe/jobs/12345"
        redirected_url = "https://job-boards.greenhouse.io/stripe"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Greenhouse", reason)

    def test_detect_lever_dropped_req_id(self):
        original_url = "https://jobs.lever.co/databricks/54321-abcd"
        redirected_url = "https://jobs.lever.co/databricks"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Lever", reason)

    def test_detect_generic_ats_drop_to_careers_portal(self):
        original_url = "https://careers.company.com/posting/backend-intern-2026"
        redirected_url = "https://careers.company.com/portal"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("generic portal", reason)

    def test_check_single_link_detects_redirect_closure(self):
        opp = {"company": "Microsoft", "role": "SWE", "apply_url": "https://jobs.careers.microsoft.com/global/en/job/1234/Role"}
        mock_resp = MagicMock()
        mock_resp.geturl.return_value = "https://apply.careers.microsoft.com/careers"
        mock_resp.read.return_value = b"<html>Search roles</html>"
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            _, is_active, reason = check_single_link(opp)
            self.assertFalse(is_active)
            self.assertIn("Microsoft", reason)

    def test_check_single_link_protected_ats(self):
        opp = {"company": "CloudflareProtected", "role": "SWE", "apply_url": "https://example.com/cf"}
        import urllib.error
        http_err = urllib.error.HTTPError("https://example.com/cf", 403, "Forbidden", {}, None)

        with patch("urllib.request.urlopen", side_effect=http_err):
            _, is_active, reason = check_single_link(opp)
            self.assertTrue(is_active)
            self.assertIn("Protected ATS (HTTP 403)", reason)

    def test_check_single_link_missing_url(self):
        opp = {"company": "NoURL", "role": "SWE"}
        _, is_active, reason = check_single_link(opp)
        self.assertFalse(is_active)
        self.assertEqual(reason, "Missing URL")

    def test_check_single_link_network_exception(self):
        opp = {"company": "TimeoutCo", "role": "SWE", "apply_url": "https://example.com/slow"}
        with patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
            _, is_active, reason = check_single_link(opp)
            self.assertTrue(is_active)
            self.assertIn("Network timeout/skip", reason)

    def test_check_single_link_active_200(self):
        opp = {"company": "LiveCo", "role": "SWE", "apply_url": "https://example.com/job"}
        mock_resp = MagicMock()
        mock_resp.geturl.return_value = "https://example.com/job"
        mock_resp.read.return_value = b"<html><body>Apply now for this role! Excellent salary.</body></html>"
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            _, is_active, reason = check_single_link(opp)
            self.assertTrue(is_active)
            self.assertEqual(reason, "Active (200 OK)")

    def test_check_single_link_whitespace_and_invalid_url(self):
        for invalid_url in ["   ", "\t\n", None, 12345]:
            opp = {"company": "BadCo", "role": "SWE", "apply_url": invalid_url}
            _, is_active, reason = check_single_link(opp)
            self.assertFalse(is_active)
            self.assertEqual(reason, "Missing URL")

    def test_is_ats_redirected_to_catalog_scheme_upgrade(self):
        orig = "http://example.com/jobs/123"
        final = "https://example.com/jobs/123"
        is_redirected, _ = is_ats_redirected_to_catalog(orig, final)
        self.assertFalse(is_redirected)

    def test_check_single_link_flags_expired_application_window(self):
        opp = {
            "id": "opp-test-cotiviti",
            "company": "Cotiviti",
            "role": "Intern AI Engineer",
            "apply_url": "https://careers-cotiviti.icims.com/jobs/19531/job"
        }

        mock_info = {
            "url": opp["apply_url"],
            "resolved_url": opp["apply_url"],
            "is_active": False,
            "reason": "Expired application window: closed on 2026-07-18",
            "position_type": "Full-Time",
            "hours_per_week": "Full-Time (40 hrs/week)",
            "deadline": datetime(2026, 7, 18),
            "is_expired": True
        }

        with patch("ats_scraper.inspect_job_page", return_value=mock_info):
            updated_opp, is_live, reason = check_single_link(opp)
            assert is_live is False
            assert "closed on 2026-07-18" in reason.lower()

    def test_check_single_link_keeps_active_when_inspect_job_page_is_active(self):
        opp = {
            "id": "opp-test-active",
            "company": "ActiveCo",
            "role": "SWE Intern",
            "apply_url": "https://careers.activeco.com/jobs/123"
        }

        mock_info = {
            "url": opp["apply_url"],
            "resolved_url": opp["apply_url"],
            "is_active": True,
            "reason": "Active (200 OK)",
            "position_type": "Internship",
            "hours_per_week": "40 hrs/week",
            "deadline": datetime(2026, 12, 31),
            "is_expired": False
        }

        mock_resp = MagicMock()
        mock_resp.geturl.return_value = opp["apply_url"]
        mock_resp.read.return_value = b"<html>Apply now</html>"
        mock_resp.__enter__.return_value = mock_resp

        with patch("ats_scraper.inspect_job_page", return_value=mock_info), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            updated_opp, is_live, reason = check_single_link(opp)
            assert is_live is True
            assert "Active" in reason



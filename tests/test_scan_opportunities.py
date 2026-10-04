import os
import sys
import unittest
from unittest.mock import patch
import tempfile
import json
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import scan_opportunities
from scan_opportunities import CandidateProfile, score_and_tier, load_candidate_profile, filter_candidate_links


class TestScanOpportunities(unittest.TestCase):
    def test_mexico_candidate_dynamic_tiering(self):
        profile = CandidateProfile(
            name="Diego Perea",
            location="Querétaro, Mexico",
            work_authorization="None",
            disallowed_industries=["crypto", "web3"]
        )
        self.assertEqual(profile.home_country_key, "mexico")
        self.assertFalse(profile.is_us_authorized)

        # Mexican role -> Tier 1
        opp_mx = {
            "company": "Salesforce",
            "role": "AI Builder Intern",
            "location": "Mexico City (Hybrid)",
            "apply_url": "https://example.com/apply1"
        }
        score, tier = score_and_tier(opp_mx, profile)
        self.assertEqual(score, 95)
        self.assertIn("Tier 1", tier)
        self.assertIn("Mexico", tier)

        # New Mexico (USA) should NOT match Mexico
        opp_new_mex = {
            "company": "Sandia Labs",
            "role": "SWE Intern",
            "location": "Albuquerque, New Mexico",
            "apply_url": "https://example.com/apply2"
        }
        score, tier = score_and_tier(opp_new_mex, profile)
        self.assertNotEqual(score, 95)
        self.assertNotIn("Tier 1", tier)

        # Remote role -> Tier 2
        opp_remote = {
            "company": "Scale AI",
            "role": "Data Annotator Intern (Remote)",
            "location": "Remote",
            "apply_url": "https://example.com/apply3"
        }
        score, tier = score_and_tier(opp_remote, profile)
        self.assertEqual(score, 85)
        self.assertIn("Tier 2", tier)

        # Canadian co-op -> Tier 4
        opp_can = {
            "company": "Capital One",
            "role": "AI Co-op",
            "location": "Toronto, ON, Canada",
            "apply_url": "https://example.com/apply4"
        }
        score, tier = score_and_tier(opp_can, profile)
        self.assertEqual(score, 75)
        self.assertIn("Tier 4", tier)

        # Top US sponsor -> Tier 3
        opp_sponsor = {
            "company": "Figma",
            "role": "Software Engineering Intern",
            "location": "San Francisco, CA",
            "apply_url": "https://example.com/apply5"
        }
        score, tier = score_and_tier(opp_sponsor, profile)
        self.assertEqual(score, 65)
        self.assertIn("Tier 3", tier)

    def test_canada_candidate_dynamic_tiering(self):
        profile = CandidateProfile(
            name="Alex Chen",
            location="Toronto, ON, Canada",
            work_authorization="None"
        )
        self.assertEqual(profile.home_country_key, "canada")

        # Canadian role -> Tier 1 for Canadian candidate
        opp_can = {
            "company": "Shopify",
            "role": "SWE Intern",
            "location": "Ottawa, Ontario, Canada",
            "apply_url": "https://example.com/apply6"
        }
        score, tier = score_and_tier(opp_can, profile)
        self.assertEqual(score, 95)
        self.assertIn("Tier 1", tier)
        self.assertIn("Canada", tier)

        # Mexico role -> Not Tier 1 for Canadian candidate
        opp_mx = {
            "company": "Mercado Libre",
            "role": "Data Analyst Intern",
            "location": "Mexico City",
            "apply_url": "https://example.com/apply7"
        }
        score, tier = score_and_tier(opp_mx, profile)
        self.assertNotEqual(score, 95)

    def test_us_authorized_candidate_tiering(self):
        profile = CandidateProfile(
            name="Sarah Smith",
            location="Austin, TX, USA",
            work_authorization="US Citizen"
        )
        self.assertTrue(profile.is_us_authorized)

        # US role with no sponsorship notes -> Tier 1
        opp_us = {
            "company": "Dell",
            "role": "Software Engineer Intern",
            "location": "Austin, TX",
            "apply_url": "https://example.com/apply8",
            "sponsorship_notes": "No visa sponsorship"
        }
        score, tier = score_and_tier(opp_us, profile)
        # Should NOT be disqualified by "no visa sponsorship" because candidate is a US citizen
        self.assertEqual(score, 95)
        self.assertIn("Tier 1", tier)

    def test_uk_and_germany_candidate_tiering(self):
        uk_profile = CandidateProfile(
            name="Emma Watson",
            location="London, United Kingdom",
            work_authorization="None"
        )
        opp_uk = {
            "company": "DeepMind",
            "role": "Research Scientist Intern",
            "location": "London, UK",
            "apply_url": "https://example.com/apply9"
        }
        score, tier = score_and_tier(opp_uk, uk_profile)
        self.assertEqual(score, 95)
        self.assertIn("Tier 1", tier)

        de_profile = CandidateProfile(
            name="Lukas Meyer",
            location="Berlin, Germany",
            work_authorization="None"
        )
        opp_de = {
            "company": "SAP",
            "role": "Developer Intern",
            "location": "Berlin, Germany",
            "apply_url": "https://example.com/apply10"
        }
        score, tier = score_and_tier(opp_de, de_profile)
        self.assertEqual(score, 95)
        self.assertIn("Tier 1", tier)

    def test_disqualifiers(self):
        profile = CandidateProfile(
            name="Test User",
            location="Toronto, Canada",
            work_authorization="None",
            disallowed_industries=["crypto", "gambling"]
        )

        # Crypto role -> Disqualified
        opp_crypto = {
            "company": "Coinbase",
            "role": "Crypto Protocol Intern",
            "location": "Remote",
            "apply_url": "https://example.com/crypto"
        }
        score, tier = score_and_tier(opp_crypto, profile)
        self.assertEqual(score, -1)
        self.assertIn("Disqualified", tier)

        # US Citizenship required on US role for non-US candidate -> Disqualified
        opp_defense = {
            "company": "Lockheed",
            "role": "Defense ML Intern",
            "location": "Denver, CO",
            "apply_url": "https://example.com/defense",
            "sponsorship_notes": "US Citizenship Required"
        }
        score, tier = score_and_tier(opp_defense, profile)
        self.assertEqual(score, -1)
        self.assertIn("Disqualified", tier)

        # Strict PhD requirement -> Disqualified
        opp_phd = {
            "company": "BioResearch",
            "role": "PhD Research Fellow (PhD Required)",
            "location": "Remote",
            "apply_url": "https://example.com/phd"
        }
        score, tier = score_and_tier(opp_phd, profile)
        self.assertEqual(score, -1)
        self.assertIn("Disqualified", tier)

    def test_placeholder_candidate_profile(self):
        # Default unconfigured profile
        profile = CandidateProfile(
            name="Candidate",
            location="City, Country",
            work_authorization="None"
        )
        self.assertTrue(profile.is_placeholder_location)

        # Arbitrary city should NOT match as domestic
        opp_random = {
            "company": "AnyCorp",
            "role": "Junior Developer",
            "location": "Amsterdam, Netherlands",
            "apply_url": "https://example.com/any"
        }
        score, tier = score_and_tier(opp_random, profile)
        self.assertNotEqual(score, 95)
        self.assertNotIn("Tier 1", tier)

        # Remote role still gets Tier 2
        opp_remote = {
            "company": "AnyCorp",
            "role": "Junior Developer",
            "location": "Remote",
            "apply_url": "https://example.com/any"
        }
        score, tier = score_and_tier(opp_remote, profile)
        self.assertEqual(score, 85)
        self.assertIn("Tier 2", tier)

    def test_load_candidate_profile_from_json(self):
        sample_data = {
            "candidate": {
                "name": "Jane Doe",
                "location": "Madrid, Spain",
                "work_authorization": "None"
            },
            "industry_domain": {
                "industries_to_avoid": ["Crypto", "Gambling"]
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_data, f)
            tmp_path = f.name

        try:
            profile = load_candidate_profile(json_path=tmp_path)
            self.assertEqual(profile.name, "Jane Doe")
            self.assertEqual(profile.raw_location, "Madrid, Spain")
            self.assertIn("crypto", profile.disallowed_industries)
            self.assertIn("gambling", profile.disallowed_industries)
            self.assertEqual(profile.home_country_key, "spain")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_sources_json_proyecto_nutria_is_disabled(self):
        sources_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts", "sources.json"))
        with open(sources_path, "r", encoding="utf-8") as f:
            sources = json.load(f)
        nutria = next((s for s in sources if s.get("id") == "proyecto-nutria-mx"), None)
        self.assertIsNotNone(nutria)
        self.assertFalse(nutria.get("enabled", True))
        self.assertIn("2024", nutria.get("note", ""))

    def test_detect_stale_upstream_feed_header(self):
        stale_content = (
            "# Summer 2024 Tech Internships by Proyecto Nutria\n"
            "This repository was created for the 2024 cycle and has been abandoned by its maintainers."
        )
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(stale_content, current_year=2026)
        self.assertTrue(is_stale)
        self.assertIn("2024", reason)

        active_content = (
            "# Summer 2027 Tech Internships\n"
            "Active community list for 2026 / 2027 internships."
        )
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(active_content, current_year=2026)
        self.assertFalse(is_stale)
        self.assertEqual(reason, "")

    def test_stale_feed_bypass_structured_json(self):
        json_content = '[{"id": 2024, "company": "Meta"}]'
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(json_content, current_year=2026)
        self.assertFalse(is_stale)
        self.assertEqual(reason, "")

        json_obj = '  {\n    "year": 2024,\n    "company": "Google"\n  }'
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(json_obj, current_year=2026)
        self.assertFalse(is_stale)
        self.assertEqual(reason, "")

    def test_stale_feed_abandoned_without_year(self):
        content = (
            "# Archived Tech Internships Repo\n"
            "This repository has been abandoned and is no longer maintained."
        )
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(content, current_year=2026)
        self.assertTrue(is_stale)
        self.assertIn("abandoned or archived", reason)

    def test_stale_feed_prior_cycle_without_active_updates(self):
        content = (
            "# Summer 2025 Tech Internships\n"
            "Collection of student developer roles."
        )
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(content, current_year=2026)
        self.assertTrue(is_stale)
        self.assertIn("expired 2025 cycle", reason)
        self.assertIn("without active 2026+ updates", reason)

    def test_filter_dead_links_with_verify_links(self):
        candidates = [
            {"company": "Active Corp", "role": "SWE Intern", "apply_url": "https://example.com/active"},
            {"company": "Dead Corp", "role": "Data Intern", "apply_url": "https://example.com/dead404"}
        ]
        def mock_checker(opp):
            if "dead404" in opp["apply_url"]:
                return opp, False, "Dead Link (HTTP 404)"
            return opp, True, "Active (200 OK)"

        verified = scan_opportunities.filter_candidate_links(candidates, checker_func=mock_checker)
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["company"], "Active Corp")

    def test_filter_candidate_links_empty_list(self):
        verified = scan_opportunities.filter_candidate_links([])
        self.assertEqual(verified, [])

    def test_filter_candidate_links_handles_checker_exception(self):
        candidates = [{"company": "CrashCo", "role": "SWE", "apply_url": "https://example.com/crash"}]
        def faulty_checker(opp):
            raise RuntimeError("Unexpected failure")

        verified = scan_opportunities.filter_candidate_links(candidates, checker_func=faulty_checker)
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["company"], "CrashCo")

    def test_filter_candidate_links_default_checker_fallback(self):
        candidates = [{"company": "LiveCo", "role": "SWE", "apply_url": "https://example.com/live"}]
        with patch("prune_opportunities.check_single_link", return_value=(candidates[0], True, "Active (200 OK)")):
            verified = scan_opportunities.filter_candidate_links(candidates, checker_func=None)
            self.assertEqual(len(verified), 1)

    def test_verify_links_cli_flag_parsing(self):
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--verify-links", action="store_true")
        args_default = parser.parse_args([])
        self.assertFalse(args_default.verify_links)
        args_flag = parser.parse_args(["--verify-links"])
        self.assertTrue(args_flag.verify_links)

    def test_score_and_tier_remote_label(self):
        item = {
            "company": "Cotiviti",
            "role": "Intern AI Engineer",
            "location": "US-Remote"
        }
        profile = CandidateProfile(location="Monterrey, Mexico", work_authorization="Needs Sponsorship")
        score, tier = score_and_tier(item, profile)
        assert score == 85
        assert "part-time" not in tier.lower()
        assert "Tier 2: Remote & Flexible Opportunities" == tier

    def test_filter_candidate_links_enriches_and_drops_expired(self):
        candidates = [
            {
                "company": "Cotiviti",
                "role": "Intern AI Engineer",
                "apply_url": "https://careers-cotiviti.icims.com/jobs/19531/job"
            },
            {
                "company": "Active Corp",
                "role": "ML Intern",
                "apply_url": "https://activecorp.com/jobs/1"
            }
        ]

        def mock_inspect(url, **kwargs):
            if "19531" in url:
                return {
                    "is_active": False,
                    "reason": "Expired application window: closed on 2026-07-18",
                    "position_type": "Full-Time",
                    "hours_per_week": "Full-Time (40 hrs/week)"
                }
            return {
                "is_active": True,
                "reason": "Active (200 OK)",
                "position_type": "Full-Time",
                "hours_per_week": "Full-Time (40 hrs/week)"
            }

        with patch("ats_scraper.inspect_job_page", side_effect=mock_inspect):
            verified = filter_candidate_links(candidates)
            assert len(verified) == 1
            assert verified[0]["company"] == "Active Corp"
            assert verified[0]["position_type"] == "Full-Time"
            assert verified[0]["hours_per_week"] == "Full-Time (40 hrs/week)"


if __name__ == "__main__":
    unittest.main()



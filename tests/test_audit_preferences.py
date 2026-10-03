import copy
import os
import sys
import tempfile
import unittest

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

from audit_preferences import (
    audit_opportunities_against_preferences,
    generate_markdown_audit_report,
)


class TestAuditPreferences(unittest.TestCase):
    def setUp(self):
        self.mock_preferences = {
            "candidate": {"name": "Candidate"},
            "availability_calendar": {
                "target_weekly_hours_max": 30,
                "target_weekly_hours_min": 20,
            },
            "location_visa": {
                "current_location": "City, Country",
                "us_work_authorization": "None",
            },
            "industry_domain": {
                "domains_of_interest": ["GenAI/LLMs", "RL", "Computer Vision"],
                "industries_to_avoid": ["Crypto"],
            },
            "deal_breakers": {
                "hard_constraints": ["No onsite 5 days/week"],
                "automatic_disqualifiers": ["US citizenship required"],
            },
        }
        self.mock_opportunities = [
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
                "company": "CryptoCo",
                "role": "Web3 Engineer",
                "tier": "Tier 2",
                "location": "Remote",
                "hours_per_week": "20",
                "status": "eligible",
                "apply_url": "https://example.com/apply2",
            },
            {
                "id": "opp-03",
                "company": "Defense Tech",
                "role": "AI Scientist",
                "tier": "Tier 3",
                "location": "Washington, DC",
                "sponsorship_notes": "US Citizenship Required",
                "hours_per_week": "40",
                "status": "eligible",
                "apply_url": "https://example.com/apply3",
            },
        ]

    def test_audit_evaluates_matches_and_disqualifications(self):
        result = audit_opportunities_against_preferences(
            self.mock_preferences, self.mock_opportunities
        )
        self.assertIn("summary", result)
        self.assertIn("matches", result)
        self.assertIn("disqualified", result)

        match_ids = [m["id"] for m in result["matches"]]
        disq_ids = [d["id"] for d in result["disqualified"]]

        self.assertIn("opp-01", match_ids)
        self.assertIn("opp-02", disq_ids)
        self.assertIn("opp-03", disq_ids)

    def test_generate_markdown_audit_report(self):
        result = audit_opportunities_against_preferences(
            self.mock_preferences, self.mock_opportunities
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f:
            temp_path = f.name
        try:
            out_file = generate_markdown_audit_report(result, output_path=temp_path)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("---\n"))
            self.assertIn("Executive Summary", content)
            self.assertIn("Salesforce", content)
            self.assertIn("Strategic Action Plan", content)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_caution_or_summer_evaluations(self):
        """Test that 40h/week semester roles and summer abroad roles needing J-1 route to caution."""
        test_opps = [
            {
                "id": "opp-40h-mexico",
                "company": "Banco MX",
                "role": "Data Analyst Intern",
                "location": "Mexico City, Mexico",
                "hours_per_week": "40",
                "status": "eligible",
            },
            {
                "id": "opp-summer-seattle",
                "company": "CloudTech",
                "role": "ML Engineer Intern",
                "location": "Seattle, WA",
                "tier": "Tier 3: Elite US Summer 2027",
                "hours_per_week": "40 (Summer 2027)",
                "status": "eligible",
            },
        ]

        result = audit_opportunities_against_preferences(
            self.mock_preferences, test_opps
        )
        caution_ids = [c["id"] for c in result["caution"]]

        self.assertIn("opp-40h-mexico", caution_ids)
        self.assertIn("opp-summer-seattle", caution_ids)
        self.assertEqual(len(result["disqualified"]), 0)

        # Check caution notes
        mex_item = [c for c in result["caution"] if c["id"] == "opp-40h-mexico"][0]
        self.assertTrue(any("exceeds" in r.lower() for r in mex_item.get("caution_reasons", [])))

        us_item = [c for c in result["caution"] if c["id"] == "opp-summer-seattle"][0]
        self.assertTrue(any("sponsorship" in r.lower() for r in us_item.get("caution_reasons", [])))

    def test_citizenship_not_required_is_not_disqualified(self):
        """Verify that negative statements like 'Citizenship not required' are not falsely disqualified."""
        test_opps = [
            {
                "id": "opp-neg-cit-01",
                "company": "OpenCorp",
                "role": "AI Research Intern",
                "location": "Remote",
                "hours_per_week": "20-30",
                "sponsorship_notes": "US Citizenship not required",
                "status": "eligible",
            },
            {
                "id": "opp-neg-cit-02",
                "company": "GlobalData",
                "role": "Data Science Intern",
                "location": "Mexico City, Mexico",
                "hours_per_week": "20",
                "key_considerations": ["Citizenship not required for international candidates"],
                "status": "eligible",
            },
        ]

        result = audit_opportunities_against_preferences(
            self.mock_preferences, test_opps
        )
        match_ids = [m["id"] for m in result["matches"]]
        disq_ids = [d["id"] for d in result["disqualified"]]

        self.assertIn("opp-neg-cit-01", match_ids)
        self.assertIn("opp-neg-cit-02", match_ids)
        self.assertNotIn("opp-neg-cit-01", disq_ids)
        self.assertNotIn("opp-neg-cit-02", disq_ids)

    def test_summer_5day_onsite_goes_to_caution_not_disqualified(self):
        """Verify summer 5-day onsite roles route to caution_or_summer, while semester onsite is disqualified."""
        test_opps = [
            {
                "id": "opp-summer-onsite",
                "company": "SummerLabs",
                "role": "Summer Research Intern",
                "location": "Mexico City",
                "work_arrangement": "Summer 2027 - 5 days/week onsite",
                "hours_per_week": "40 (Summer)",
                "status": "eligible",
            },
            {
                "id": "opp-semester-onsite",
                "company": "FallLabs",
                "role": "Fall Data Intern",
                "location": "Monterrey, Mexico",
                "work_arrangement": "5 days/week onsite",
                "hours_per_week": "20",
                "status": "eligible",
            },
        ]

        result = audit_opportunities_against_preferences(
            self.mock_preferences, test_opps
        )
        caution_ids = [c["id"] for c in result["caution"]]
        disq_ids = [d["id"] for d in result["disqualified"]]

        self.assertIn("opp-summer-onsite", caution_ids)
        self.assertNotIn("opp-summer-onsite", disq_ids)

        self.assertIn("opp-semester-onsite", disq_ids)
        self.assertNotIn("opp-semester-onsite", caution_ids)

    def test_empty_opportunities_and_dynamic_action_plan(self):
        """Verify empty opportunity inputs work gracefully and action plan is dynamic."""
        empty_result = audit_opportunities_against_preferences(
            self.mock_preferences, []
        )
        self.assertEqual(empty_result["total_analyzed"], 0)
        self.assertEqual(empty_result["summary"]["direct_matches"], 0)
        self.assertEqual(empty_result["summary"]["caution_or_summer"], 0)
        self.assertEqual(empty_result["summary"]["disqualified"], 0)

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f:
            temp_path = f.name
        try:
            out_file = generate_markdown_audit_report(empty_result, output_path=temp_path)
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("No direct immediate matches identified", content)
            self.assertIn("No direct semester matches currently active", content)

            # Test report with populated matches and caution to verify dynamic companies
            populated_result = audit_opportunities_against_preferences(
                self.mock_preferences,
                [
                    {
                        "id": "opp-dyn-01",
                        "company": "AcmeAI",
                        "role": "LLM Intern",
                        "location": "Remote",
                        "hours_per_week": "20",
                        "status": "eligible",
                    },
                    {
                        "id": "opp-dyn-02",
                        "company": "BetaRobotics",
                        "role": "Robotics Intern",
                        "location": "Boston, MA",
                        "hours_per_week": "40 (Summer)",
                        "status": "eligible",
                    },
                ],
            )
            out_file2 = generate_markdown_audit_report(populated_result, output_path=temp_path)
            with open(out_file2, "r", encoding="utf-8") as f:
                content2 = f.read()
            self.assertIn("AcmeAI", content2)
            self.assertIn("BetaRobotics", content2)
            # Both should appear under Strategic Action Plan dynamically
            action_plan_idx = content2.find("## Strategic Action Plan")
            self.assertTrue(action_plan_idx != -1)
            action_section = content2[action_plan_idx:]
            self.assertIn("AcmeAI", action_section)
            self.assertIn("BetaRobotics", action_section)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_elastic_candidate_location_matching(self):
        """Verify candidate location matching dynamically adapts to any country/city."""
        # 1. Candidate in Canada
        canada_prefs = copy.deepcopy(self.mock_preferences)
        canada_prefs["location_visa"]["current_location"] = "Toronto, Ontario, Canada"
        canada_prefs["location_visa"]["us_work_authorization"] = "None"

        test_opps = [
            {
                "id": "opp-toronto",
                "company": "Shopify",
                "role": "Data Engineer Intern",
                "location": "Toronto, ON (Hybrid)",
                "hours_per_week": "20",
                "status": "eligible",
            },
            {
                "id": "opp-mexico-onsite",
                "company": "Kavak",
                "role": "Software Engineer Intern",
                "location": "Mexico City, Mexico (Onsite)",
                "hours_per_week": "20",
                "status": "eligible",
            },
        ]

        result_canada = audit_opportunities_against_preferences(canada_prefs, test_opps)
        match_ids_canada = [m["id"] for m in result_canada["matches"]]
        caution_ids_canada = [c["id"] for c in result_canada["caution"]]

        self.assertIn("opp-toronto", match_ids_canada)
        self.assertIn("opp-mexico-onsite", caution_ids_canada)

        # 2. Candidate in US with US Work Authorization
        us_prefs = copy.deepcopy(self.mock_preferences)
        us_prefs["location_visa"]["current_location"] = "Austin, TX, USA"
        us_prefs["location_visa"]["us_work_authorization"] = "Citizen / Green Card"

        us_opps = [
            {
                "id": "opp-austin",
                "company": "Dell",
                "role": "ML Intern",
                "location": "Austin, TX (Hybrid)",
                "hours_per_week": "20",
                "status": "eligible",
            },
            {
                "id": "opp-remote-us",
                "company": "Amazon",
                "role": "Software Intern",
                "location": "Remote (US)",
                "hours_per_week": "20",
                "status": "eligible",
            },
            {
                "id": "opp-seattle-onsite",
                "company": "Microsoft",
                "role": "Software Intern",
                "location": "Seattle, WA (Onsite)",
                "hours_per_week": "20",
                "status": "eligible",
            },
        ]

        result_us = audit_opportunities_against_preferences(us_prefs, us_opps)
        match_ids_us = [m["id"] for m in result_us["matches"]]
        caution_ids_us = [c["id"] for c in result_us["caution"]]
        self.assertIn("opp-austin", match_ids_us)
        self.assertIn("opp-remote-us", match_ids_us)
        self.assertIn("opp-seattle-onsite", caution_ids_us)


if __name__ == "__main__":
    unittest.main()

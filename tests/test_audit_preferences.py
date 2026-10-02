import unittest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "preference-manager", "scripts")))

from audit_preferences import audit_opportunities_against_preferences, generate_markdown_audit_report

class TestAuditPreferences(unittest.TestCase):
    def setUp(self):
        self.mock_preferences = {
            "candidate": {"name": "Diego Perea León"},
            "availability_calendar": {"target_weekly_hours_max": 30, "target_weekly_hours_min": 20},
            "location_visa": {"current_location": "Querétaro, Mexico", "us_work_authorization": "None"},
            "industry_domain": {
                "domains_of_interest": ["GenAI/LLMs", "RL", "Computer Vision"],
                "industries_to_avoid": ["Crypto"]
            },
            "deal_breakers": {
                "hard_constraints": ["No onsite 5 days/week"],
                "automatic_disqualifiers": ["US citizenship required"]
            }
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
                "apply_url": "https://example.com/apply1"
            },
            {
                "id": "opp-02",
                "company": "CryptoCo",
                "role": "Web3 Engineer",
                "tier": "Tier 2",
                "location": "Remote",
                "hours_per_week": "20",
                "status": "eligible",
                "apply_url": "https://example.com/apply2"
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
                "apply_url": "https://example.com/apply3"
            }
        ]

    def test_audit_evaluates_matches_and_disqualifications(self):
        result = audit_opportunities_against_preferences(self.mock_preferences, self.mock_opportunities)
        self.assertIn("summary", result)
        self.assertIn("matches", result)
        self.assertIn("disqualified", result)

        match_ids = [m["id"] for m in result["matches"]]
        disq_ids = [d["id"] for d in result["disqualified"]]

        self.assertIn("opp-01", match_ids)
        self.assertIn("opp-02", disq_ids)
        self.assertIn("opp-03", disq_ids)

    def test_generate_markdown_audit_report(self):
        result = audit_opportunities_against_preferences(self.mock_preferences, self.mock_opportunities)
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
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()

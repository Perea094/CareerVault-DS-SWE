import os
import unittest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "application-tracker", "scripts")))
import track_application

class TestApplicationTracker(unittest.TestCase):
    def test_valid_statuses(self):
        self.assertIn("wishlist", track_application.VALID_STATUSES)
        self.assertIn("applied", track_application.VALID_STATUSES)
        self.assertIn("interview", track_application.VALID_STATUSES)
        self.assertIn("offer", track_application.VALID_STATUSES)
        self.assertIn("rejected", track_application.VALID_STATUSES)

    def test_update_application_status(self):
        data = {
            "opportunities": [
                {"id": "opp-1", "company": "Figma", "status": "eligible", "pipeline_status": "wishlist"}
            ]
        }
        updated = track_application.update_opportunity_pipeline(
            data,
            opp_id="opp-1",
            new_status="applied",
            date_applied="2026-10-02",
            notes="Applied via portal with tailored CV"
        )
        opp = updated["opportunities"][0]
        self.assertEqual(opp["pipeline_status"], "applied")
        self.assertEqual(opp["date_applied"], "2026-10-02")
        self.assertEqual(opp["pipeline_notes"], "Applied via portal with tailored CV")

    def test_generate_kanban_markdown(self):
        opportunities = [
            {"company": "Figma", "role": "Data Scientist", "pipeline_status": "applied", "apply_url": "https://figma.com"},
            {"company": "Google", "role": "SWE Intern", "pipeline_status": "interview", "apply_url": "https://google.com"}
        ]
        md = track_application.generate_pipeline_dashboard(opportunities)
        self.assertIn("# Application Pipeline Dashboard", md)
        self.assertIn("## Applied", md)
        self.assertIn("## Interview", md)
        self.assertIn("Figma", md)
        self.assertIn("Google", md)

    def test_invalid_status_raises_error(self):
        data = {
            "opportunities": [
                {"id": "opp-1", "company": "Figma", "pipeline_status": "wishlist"}
            ]
        }
        with self.assertRaises(ValueError):
            track_application.update_opportunity_pipeline(
                data,
                opp_id="opp-1",
                new_status="invalid_status"
            )

    def test_opp_not_found_raises_error(self):
        data = {
            "opportunities": [
                {"id": "opp-1", "company": "Figma", "pipeline_status": "wishlist"}
            ]
        }
        with self.assertRaises(ValueError):
            track_application.update_opportunity_pipeline(
                data,
                opp_id="nonexistent-id",
                new_status="applied"
            )

    def test_dashboard_with_dict_input(self):
        data = {
            "opportunities": [
                {"company": "Apple", "role": "ML Intern", "pipeline_status": "wishlist"}
            ]
        }
        md = track_application.generate_pipeline_dashboard(data)
        self.assertIn("# Application Pipeline Dashboard", md)
        self.assertIn("## Wishlist", md)
        self.assertIn("Apple", md)

    def test_save_and_load_database(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_db = Path(tmpdir) / "test_opps.json"
            tmp_csv = Path(tmpdir) / "test_opps.csv"
            payload = {
                "opportunities": [
                    {
                        "id": "opp-test",
                        "company": "TestCorp",
                        "role": "Engineer",
                        "pipeline_status": "applied"
                    }
                ]
            }
            track_application.save_database(payload, primary_path=tmp_db, mirror_path=None, csv_path=tmp_csv)
            self.assertTrue(tmp_db.exists())
            self.assertTrue(tmp_csv.exists())

            loaded = track_application.load_database(tmp_db)
            self.assertEqual(len(loaded["opportunities"]), 1)
            self.assertEqual(loaded["opportunities"][0]["company"], "TestCorp")

if __name__ == "__main__":
    unittest.main()

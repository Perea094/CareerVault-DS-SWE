import unittest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "preference-manager", "scripts")))

from preference_models import (
    PreferenceModel,
    load_preferences_json,
    save_preferences_json,
    sync_to_markdown,
    load_preferences_from_markdown,
    DEFAULT_PREFERENCES
)

class TestPreferenceModels(unittest.TestCase):
    def test_default_preferences_structure(self):
        pref = DEFAULT_PREFERENCES
        self.assertIn("availability_calendar", pref)
        self.assertIn("weekly_grid", pref["availability_calendar"])
        self.assertEqual(len(pref["availability_calendar"]["time_slots"]), 32)
        self.assertEqual(pref["availability_calendar"]["time_slots"][0]["label"], "06:00 - 06:30")
        self.assertEqual(pref["availability_calendar"]["time_slots"][-1]["label"], "21:30 - 22:00")
        self.assertIn("work_arrangement", pref)
        self.assertIn("location_visa", pref)
        self.assertIn("compensation_benefits", pref)
        self.assertIn("domains_of_interest", pref["industry_domain"])
        self.assertIn("hard_constraints", pref["deal_breakers"])

    def test_calculate_available_hours(self):
        model = PreferenceModel(DEFAULT_PREFERENCES)
        hours = model.calculate_available_hours()
        self.assertIsInstance(hours, (int, float))
        self.assertGreaterEqual(hours, 0)
        self.assertEqual(hours, 30.0)

    def test_json_roundtrip(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            temp_path = f.name
        try:
            save_preferences_json(DEFAULT_PREFERENCES, temp_path)
            loaded = load_preferences_json(temp_path)
            self.assertEqual(loaded["candidate"]["name"], DEFAULT_PREFERENCES["candidate"]["name"])
            self.assertEqual(loaded["work_arrangement"]["preference_rank"], ["Remote", "Hybrid", "Onsite"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_sync_to_markdown_preserves_flat_yaml(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f:
            temp_md_path = f.name
        try:
            model = PreferenceModel(DEFAULT_PREFERENCES)
            sync_to_markdown(model.data, temp_md_path)
            with open(temp_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertTrue(content.startswith("---\n"))
            self.assertIn("work_preference_rank:", content)
            self.assertIn("- Remote", content)
            self.assertIn("minimum_hourly: 20", content)
            self.assertIn("current_location: \"Querétaro, Mexico\"", content)
            frontmatter = content.split("---")[1]
            self.assertNotIn("work_arrangement:", frontmatter)
            self.assertNotIn("location_visa:", frontmatter)
            self.assertIn("# Narrative Context", content)
            self.assertIn("on team size", content)
        finally:
            if os.path.exists(temp_md_path):
                os.remove(temp_md_path)

    def test_markdown_roundtrip_preserves_data_and_calendar(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f:
            temp_md_path = f.name
        try:
            sync_to_markdown(DEFAULT_PREFERENCES, temp_md_path)
            reloaded = load_preferences_from_markdown(temp_md_path, base_data=DEFAULT_PREFERENCES)
            self.assertEqual(reloaded["work_arrangement"]["preference_rank"], ["Remote", "Hybrid", "Onsite"])
            self.assertEqual(reloaded["compensation_benefits"]["minimum_hourly"], 20)
            self.assertEqual(reloaded["location_visa"]["current_location"], "Querétaro, Mexico")
            self.assertEqual(reloaded["version"], "1.1")
            self.assertEqual(reloaded["status"], "active")
            self.assertIn("weekly_grid", reloaded["availability_calendar"])
            self.assertEqual(len(reloaded["availability_calendar"]["time_slots"]), 32)
            self.assertEqual(reloaded["availability_calendar"]["weekly_grid"]["monday"]["14_00"], "available")
            self.assertIn("# Narrative Context", reloaded.get("narrative_context", ""))
        finally:
            if os.path.exists(temp_md_path):
                os.remove(temp_md_path)

if __name__ == "__main__":
    unittest.main()

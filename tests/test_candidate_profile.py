import os
import unittest
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "001-background")))
import candidate_profile

class TestCandidateProfile(unittest.TestCase):
    def test_load_candidate_profile_from_json(self):
        sample_data = {
            "candidate": {
                "name": "Jane Doe",
                "school": "Stanford University",
                "degree": "B.S. in Computer Science",
                "graduation": "June 2027",
                "location": "Palo Alto, CA",
                "work_authorization": "US Citizen",
                "email": "jane@stanford.edu",
                "phone": "+1 650 555 0199",
                "linkedin": "https://linkedin.com/in/janedoe",
                "github": "https://github.com/janedoe"
            },
            "career_goals": {
                "target_domains": ["Distributed Systems", "AI Infrastructure"]
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_data, f)
            tmp_path = Path(f.name)
            
        try:
            profile = candidate_profile.load_profile(tmp_path)
            self.assertEqual(profile["name"], "Jane Doe")
            self.assertEqual(profile["school"], "Stanford University")
            self.assertEqual(profile["degree"], "B.S. in Computer Science")
            self.assertEqual(profile["email"], "jane@stanford.edu")
            self.assertIn("Distributed Systems", profile["target_domains"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_fallback_defaults_when_empty(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({}, f)
            tmp_path = Path(f.name)
            
        try:
            profile = candidate_profile.load_profile(tmp_path)
            self.assertEqual(profile["name"], "Candidate")
            self.assertEqual(profile["degree"], "B.S. in Computer Science / Data Science")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_academic_context_and_international_visa_fallbacks(self):
        sample_data = {
            "academic_context": {
                "university": "Oxford University",
                "program": "M.Sc. in Advanced Computer Science",
                "expected_graduation": "September 2027"
            },
            "location_visa": {
                "current_location": "Oxford, UK",
                "work_authorization": "UK Citizen / EU Pre-settled",
                "us_work_authorization": "None"
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_data, f)
            tmp_path = Path(f.name)

        try:
            profile = candidate_profile.load_profile(tmp_path)
            self.assertEqual(profile["school"], "Oxford University")
            self.assertEqual(profile["university"], "Oxford University")
            self.assertEqual(profile["degree"], "M.Sc. in Advanced Computer Science")
            self.assertEqual(profile["major"], "M.Sc. in Advanced Computer Science")
            self.assertEqual(profile["graduation"], "September 2027")
            self.assertEqual(profile["location"], "Oxford, UK")
            self.assertEqual(profile["work_authorization"], "UK Citizen / EU Pre-settled")
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_canonical_schema_prioritization_over_legacy(self):
        sample_data = {
            "compensation_benefits": {
                "minimum_hourly": 55.0
            },
            "compensation": {
                "minimum_hourly_usd": 20.0
            },
            "industry_domain": {
                "domains_of_interest": ["GenAI/LLMs", "Robotics"]
            },
            "career_goals": {
                "target_domains": ["Legacy Domain"]
            }
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(sample_data, f)
            tmp_path = Path(f.name)

        try:
            profile = candidate_profile.load_profile(tmp_path)
            self.assertEqual(profile["compensation_floor"], 55.0)
            self.assertEqual(profile["target_domains"], ["GenAI/LLMs", "Robotics"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()


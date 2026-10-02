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

if __name__ == "__main__":
    unittest.main()

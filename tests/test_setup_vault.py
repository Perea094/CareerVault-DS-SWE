import os
import unittest
from unittest.mock import patch
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import setup_vault

class TestSetupVault(unittest.TestCase):
    def test_configure_vault_non_interactive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            bg_dir = vault_path / "001-background"
            cv_dir = vault_path / "002-cv"
            bg_dir.mkdir()
            cv_dir.mkdir()
            
            template_path = cv_dir / "template.tex"
            template_path.write_text(r"\textbf{<<NAME>>} -- <<DEGREE>>", encoding="utf-8")
            
            profile_input = {
                "name": "Maria Gonzalez",
                "school": "MIT",
                "degree": "B.S. in Artificial Intelligence and Decision Making",
                "graduation": "June 2026",
                "location": "Cambridge, MA",
                "work_authorization": "US Citizen",
                "email": "maria@mit.edu",
                "phone": "+1 617 555 0144",
                "linkedin": "https://linkedin.com/in/mariag",
                "github": "https://github.com/mariag",
                "minimum_hourly_usd": 30.0,
                "target_domains": ["Computer Vision", "Robotics"]
            }
            
            result = setup_vault.configure_vault(
                vault_dir=vault_path,
                profile=profile_input,
                dry_run=False
            )
            
            self.assertTrue(result["success"])
            prefs_json = bg_dir / "preferences.json"
            self.assertTrue(prefs_json.exists())
            
            with open(prefs_json, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["candidate"]["name"], "Maria Gonzalez")
            self.assertEqual(saved["candidate"]["school"], "MIT")
            
            generated_tex = cv_dir / "Maria_Gonzalez_Resume.tex"
            self.assertTrue(generated_tex.exists())
            self.assertIn("Maria Gonzalez", generated_tex.read_text(encoding="utf-8"))

    def test_dry_run_does_not_modify_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            bg_dir = vault_path / "001-background"
            cv_dir = vault_path / "002-cv"
            bg_dir.mkdir()
            cv_dir.mkdir()
            
            profile_input = {"name": "Test User"}
            result = setup_vault.configure_vault(vault_dir=vault_path, profile=profile_input, dry_run=True)
            self.assertTrue(result["dry_run"])
            self.assertFalse((bg_dir / "preferences.json").exists())

    def test_interactive_wizard_inputs(self):
        inputs = [
            "John Developer",
            "UC Berkeley",
            "B.S. in EECS",
            "December 2026",
            "Berkeley, CA",
            "US Citizen",
            "john@berkeley.edu",
            "+1 510 555 0199",
            "https://linkedin.com/in/johndev",
            "https://github.com/johndev"
        ]
        with patch("builtins.input", side_effect=inputs):
            profile = setup_vault.interactive_wizard()
            self.assertEqual(profile["name"], "John Developer")
            self.assertEqual(profile["school"], "UC Berkeley")
            self.assertEqual(profile["degree"], "B.S. in EECS")
            self.assertEqual(profile["email"], "john@berkeley.edu")
            self.assertIn("Software Engineering", profile["target_domains"])

    def test_configure_vault_preserves_existing_schedule(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_path = Path(tmpdir)
            bg_dir = vault_path / "001-background"
            bg_dir.mkdir()
            
            prefs_json = bg_dir / "preferences.json"
            initial_data = {
                "schedule": {"custom_rule": "keep_intact"},
                "modality": {"ranking": ["onsite", "hybrid", "remote"]}
            }
            with open(prefs_json, "w", encoding="utf-8") as f:
                json.dump(initial_data, f)
                
            profile_input = {"name": "Existing User"}
            result = setup_vault.configure_vault(vault_dir=vault_path, profile=profile_input)
            self.assertTrue(result["success"])
            
            with open(prefs_json, "r", encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved["schedule"]["custom_rule"], "keep_intact")
            self.assertEqual(saved["modality"]["ranking"], ["onsite", "hybrid", "remote"])

if __name__ == "__main__":
    unittest.main()

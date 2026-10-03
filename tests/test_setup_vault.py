import os
import unittest
from unittest.mock import patch, MagicMock
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

    def test_check_missing_dependencies(self):
        def fake_import(name, *args, **kwargs):
            if name == "pypdfium2":
                raise ImportError("Mocked missing package")
            return MagicMock()

        with patch("builtins.__import__", side_effect=fake_import):
            missing = setup_vault.check_missing_dependencies()
            self.assertIn("pypdfium2", missing)

    def test_get_venv_executables(self):
        venv_path = Path("/mock/vault/.venv")
        with patch("os.name", "nt"):
            py_bin, pip_bin = setup_vault.get_venv_executables(venv_path)
            self.assertEqual(py_bin, venv_path / "Scripts" / "python.exe")
            self.assertEqual(pip_bin, venv_path / "Scripts" / "pip.exe")

        with patch("os.name", "posix"):
            py_bin, pip_bin = setup_vault.get_venv_executables(venv_path)
            self.assertEqual(py_bin, venv_path / "bin" / "python")
            self.assertEqual(pip_bin, venv_path / "bin" / "pip")

    def test_auto_setup_environment_in_active_venv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_root = Path(tmpdir)
            req_file = vault_root / "requirements.txt"
            req_file.write_text("pytest\n", encoding="utf-8")

            with patch("sys.prefix", "/custom/venv"), patch("sys.base_prefix", "/usr"):
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    success = setup_vault.auto_setup_environment(vault_root)
                    self.assertTrue(success)
                    mock_run.assert_called_once()
                    cmd = mock_run.call_args[0][0]
                    self.assertIn("pip", cmd)
                    self.assertIn(str(req_file), cmd)

    def test_auto_setup_environment_handles_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_root = Path(tmpdir)
            with patch("sys.prefix", "/custom/venv"), patch("sys.base_prefix", "/usr"):
                with patch("subprocess.run", side_effect=Exception("Pip network failure")):
                    success = setup_vault.auto_setup_environment(vault_root)
                    self.assertFalse(success)

    def test_launch_preferences_server(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_root = Path(tmpdir)
            script_path = vault_root / ".agents" / "skills" / "preference-manager" / "scripts" / "preference_server.py"
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text("# Mock server", encoding="utf-8")

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                success = setup_vault.launch_preferences_server(vault_root, open_browser=True)
                self.assertTrue(success)
                mock_run.assert_called_once()
                cmd = mock_run.call_args[0][0]
                self.assertIn(str(script_path), cmd)
                self.assertIn("--open", cmd)

    def test_launch_preferences_server_missing_script(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_root = Path(tmpdir)
            success = setup_vault.launch_preferences_server(vault_root, open_browser=True)
            self.assertFalse(success)

if __name__ == "__main__":
    unittest.main()


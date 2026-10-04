import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "002-cv", "scripts")))
import validate_ats

class TestValidateAts(unittest.TestCase):
    def test_extract_text_and_metrics(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Candidate Name\n"
            "City, Country • candidate@example.com • +1 555 123 4567\n"
            "EDUCATION\nUniversity of Technology\n"
            "EXPERIENCE\nData Science Experience\n"
            "PROJECTS\nMachine Learning Pipeline\n"
            "SKILLS\nPython, C++, PyTorch\n"
        )
        mock_page.width = 612.0
        mock_page.height = 792.0
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        
        with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
            result = validate_ats.scan_pdf_for_ats(Path("002-cv/resume.pdf"))
            
            self.assertTrue(result["is_single_page"])
            self.assertEqual(result["page_count"], 1)
            self.assertTrue(result["has_contact_info"]["email"])
            self.assertTrue(result["has_contact_info"]["phone"])
            self.assertIn("education", result["sections_found"])
            self.assertIn("experience", result["sections_found"])
            self.assertIn("projects", result["sections_found"])
            self.assertIn("skills", result["sections_found"])
            self.assertEqual(result["ats_score"], 100)

    def test_flag_missing_sections(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Only Some Random Text without headers"
        mock_page.width = 612.0
        mock_page.height = 792.0
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        
        with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
            result = validate_ats.scan_pdf_for_ats(Path("002-cv/resume.pdf"))
            self.assertLess(result["ats_score"], 60)
            self.assertFalse(result["has_contact_info"]["email"])

    def test_flag_multi_page(self):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 Content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 Content"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        
        with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
            result = validate_ats.scan_pdf_for_ats(Path("002-cv/resume.pdf"))
            self.assertFalse(result["is_single_page"])
            self.assertEqual(result["page_count"], 2)
            self.assertTrue(any("Resume exceeds 1 page" in w for w in result["warnings"]))

    def test_contact_info_github_linkedin(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Candidate Name\n"
            "user@domain.com • +1 234 567 8900 • github.com/candidate • linkedin.com/in/candidate\n"
            "EDUCATION\nTech University\n"
            "EXPERIENCE\nSoftware Engineer\n"
            "PROJECTS\nAI Tool\n"
            "SKILLS\nPython\n"
        )
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
            result = validate_ats.scan_pdf_for_ats(Path("dummy.pdf"))
            self.assertTrue(result["has_contact_info"]["github"])
            self.assertTrue(result["has_contact_info"]["linkedin"])
            self.assertEqual(result["density_metrics"]["density_status"], "sparse")

    def test_cli_json_and_exit_code_pass(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Candidate\n"
            "candidate@example.com • +1 555 0100\n"
            "EDUCATION\nUniversity\n"
            "EXPERIENCE\nCompany\n"
            "PROJECTS\nProject\n"
            "SKILLS\nPython\n"
        )
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        with patch("pathlib.Path.exists", return_value=True):
            with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
                with patch("sys.argv", ["validate_ats.py", "--pdf", "test.pdf", "--json"]):
                    with patch("builtins.print") as mock_print:
                        with self.assertRaises(SystemExit) as cm:
                            validate_ats.main()
                        self.assertEqual(cm.exception.code, 0)
                        mock_print.assert_called()

    def test_cli_exit_code_fail(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Random text"
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        with patch("pathlib.Path.exists", return_value=True):
            with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
                with patch("sys.argv", ["validate_ats.py", "--pdf", "test.pdf"]):
                    with patch("builtins.print"):
                        with self.assertRaises(SystemExit) as cm:
                            validate_ats.main()
                        self.assertEqual(cm.exception.code, 1)

    def test_scan_text_and_markdown_resume(self):
        sample_md = """# Taylor Swift
taylor@domain.edu • +1 555 0100 • github.com/taylor • linkedin.com/in/taylor

## Education
University of Science
B.S. in Computer Science

## Experience
Software Engineer at Cloud Tech
- Built scalable streaming pipeline processing 10M events daily.

## Projects
Distributed Cache
- Built Redis-compatible caching engine in Rust.

## Skills
Python, Rust, Distributed Systems, Linux
"""
        result = validate_ats.scan_text_for_ats(sample_md, file_path="sample.md")
        self.assertEqual(result["ats_score"], 100)
        self.assertTrue(result["is_single_page"])
        self.assertTrue(result["has_contact_info"]["email"])
        self.assertTrue(result["has_contact_info"]["phone"])
        self.assertTrue(result["has_contact_info"]["github"])
        self.assertTrue(result["has_contact_info"]["linkedin"])
        self.assertIn("education", result["sections_found"])
        self.assertIn("experience", result["sections_found"])
        self.assertIn("projects", result["sections_found"])
        self.assertIn("skills", result["sections_found"])

    def test_scan_resume_dispatches_by_extension(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = Path(tmpdir) / "test.tex"
            tex_file.write_text(r"""
\documentclass{article}
\begin{document}
Candidate
user@example.com -- +1 555 0122
\cvsection{Education} University
\cvsection{Experience} Work
\cvsection{Projects} Code
\cvsection{Technical Skills} Python
\end{document}
""", encoding="utf-8")
            result = validate_ats.scan_resume(tex_file)
            self.assertEqual(result["ats_score"], 100)
            self.assertEqual(result["file_path"], str(tex_file))

    def test_detect_abstract_placeholders_flags_unpopulated_template(self):
        sample_tex = r"""
\documentclass{article}
\begin{document}
Candidate
candidate@example.com -- +1 555 0100
\cvsection{Education} University of Technology
\cvsection{Experience}
\textbf{[Company / Organization Name]}
\begin{itemize}
    \item [Action Verb] engineered pipeline.
\end{itemize}
\cvsection{Projects}
\textbf{[Key Technical Project 1]}
\cvsection{Skills} Python
\end{document}
"""
        result = validate_ats.scan_text_for_ats(sample_tex, file_path="template.tex")
        self.assertTrue(result["placeholders_detected"])
        self.assertGreaterEqual(len(result["detected_placeholders"]), 2)
        self.assertEqual(result["ats_score"], 0)
        self.assertFalse(result["is_ready_for_application"])
        self.assertTrue(any("Abstract template placeholders detected" in w for w in result["warnings"]))

    def test_detect_clean_resume_without_placeholders_passes(self):
        sample_md = """# Taylor Swift
taylor@domain.edu • +1 555 0100 • github.com/taylor • linkedin.com/in/taylor

## Education
University of Science
B.S. in Computer Science

## Experience
Software Engineer at Cloud Tech
- Built scalable streaming pipeline processing 10M events daily.

## Projects
Distributed Cache
- Built Redis-compatible caching engine in Rust.

## Skills
Python, Rust, Distributed Systems, Linux
"""
        result = validate_ats.scan_text_for_ats(sample_md, file_path="sample.md")
        self.assertFalse(result["placeholders_detected"])
        self.assertEqual(len(result["detected_placeholders"]), 0)
        self.assertEqual(result["ats_score"], 100)
        self.assertTrue(result["is_ready_for_application"])

    def test_vault_background_check_reports_counts(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            vault_root = Path(tmpdir)
            exp_dir = vault_root / "001-background" / "experiences"
            proj_dir = vault_root / "001-background" / "projects"
            edu_dir = vault_root / "001-background" / "education"
            exp_dir.mkdir(parents=True, exist_ok=True)
            proj_dir.mkdir(parents=True, exist_ok=True)
            edu_dir.mkdir(parents=True, exist_ok=True)

            (exp_dir / ".gitkeep").write_text("", encoding="utf-8")
            (exp_dir / "exp1.md").write_text("# Exp 1", encoding="utf-8")
            (proj_dir / "proj1.md").write_text("# Proj 1", encoding="utf-8")
            (proj_dir / "proj2.md").write_text("# Proj 2", encoding="utf-8")
            (edu_dir / "edu1.md").write_text("# Edu 1", encoding="utf-8")

            status = validate_ats.check_vault_background(vault_root)
            self.assertEqual(status["experiences_count"], 1)
            self.assertEqual(status["projects_count"], 2)
            self.assertEqual(status["education_count"], 1)
            self.assertFalse(status["is_background_empty"])

    def test_format_text_report_with_placeholders(self):
        result = {
            "file_path": "002-cv/template.tex",
            "ats_score": 0,
            "page_count": 1,
            "is_single_page": True,
            "word_count": 300,
            "density_metrics": {"density_status": "optimal"},
            "sections_found": ["education", "experience"],
            "sections_missing": ["projects", "skills"],
            "has_contact_info": {"email": True, "phone": True, "github": False, "linkedin": False},
            "placeholders_detected": True,
            "detected_placeholders": ["[Company / Organization Name]", "[Action Verb]"],
            "background_status": {"experiences_count": 3, "projects_count": 4, "is_background_empty": False},
            "is_ready_for_application": False,
            "warnings": ["Abstract template placeholders detected ([Company / Organization Name], [Action Verb]). Verified candidate background has not been ingested yet."],
        }
        report = validate_ats.format_text_report(result)
        self.assertIn("ATS Score:        0/100 (BLOCKED - UNPOPULATED TEMPLATE)", report)
        self.assertIn("Template Status:  ABSTRACT PLACEHOLDERS DETECTED (Background Ingestion Required)", report)
        self.assertIn("Verified Records: 3 experiences, 4 projects in 001-background/", report)
        self.assertIn("• [MANDATORY NEXT STEP] Ingest your verified background into 001-background/ using the 'add-experience-curriculum' skill before tailoring CVs.", report)

    def test_detect_placeholders_patterns(self):
        text = (
            "<<NAME>> and <<EMAIL>>\n"
            "[Company / Organization Name]\n"
            "[Role / Title]\n"
            "[Action Verb]\n"
            "[Key Technical Project 1]\n"
            "[Project Title]\n"
            "[Start Month Year]\n"
            "achieved [X%]\n"
            "[Languages: Python, Go]\n"
            "[Frameworks & Libraries: PyTorch]\n"
            "[Infrastructure: Docker]\n"
            "[Honors / Scholarships: Merit Scholar]\n"
            "[Relevant Core Coursework: Distributed Systems]\n"
        )
        detected = validate_ats.detect_placeholders(text)
        self.assertIn("<<NAME>>", detected)
        self.assertIn("<<EMAIL>>", detected)
        self.assertIn("[Company / Organization Name]", detected)
        self.assertIn("[Role / Title]", detected)
        self.assertIn("[Action Verb]", detected)
        self.assertIn("[Key Technical Project 1]", detected)
        self.assertIn("[Project Title]", detected)
        self.assertIn("[Start Month Year]", detected)
        self.assertIn("[X%]", detected)
        self.assertIn("[Languages: Python, Go]", detected)
        self.assertIn("[Frameworks & Libraries: PyTorch]", detected)
        self.assertIn("[Infrastructure: Docker]", detected)
        self.assertIn("[Honors / Scholarships: Merit Scholar]", detected)
        self.assertIn("[Relevant Core Coursework: Distributed Systems]", detected)

    def test_vault_background_empty_warning(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_vault = Path(tmpdir)
            sample_md = """# Candidate Name\nuser@example.com • +1 555 0100\n## Education\nUniv\n## Experience\nJob\n## Projects\nProj\n## Skills\nPython\n"""
            result = validate_ats.scan_text_for_ats(sample_md, file_path="sample.md", vault_root=empty_vault)
            self.assertTrue(result["background_status"]["is_background_empty"])
            self.assertTrue(any("001-background/ has 0 verified experience or project notes." in w for w in result["warnings"]))

    def test_cli_exit_code_blocked_by_placeholders(self):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Candidate\n"
            "candidate@example.com • +1 555 0100\n"
            "EDUCATION\nUniversity\n"
            "EXPERIENCE\n[Company / Organization Name]\n[Action Verb] developed system\n"
            "PROJECTS\nProject\n"
            "SKILLS\nPython\n"
        )
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]

        with patch("pathlib.Path.exists", return_value=True):
            with patch("validate_ats.pdfplumber.open", return_value=mock_pdf):
                with patch("sys.argv", ["validate_ats.py", "--pdf", "test.pdf"]):
                    with patch("builtins.print"):
                        with self.assertRaises(SystemExit) as cm:
                            validate_ats.main()
                        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()

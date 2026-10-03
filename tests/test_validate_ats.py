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

if __name__ == "__main__":
    unittest.main()

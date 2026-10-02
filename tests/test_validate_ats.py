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
            "Diego Perea León\n"
            "Querétaro, Mexico • a01708350@tec.mx • +52 442 2713186\n"
            "EDUCATION\nTecnológico de Monterrey\n"
            "EXPERIENCE\nDatabricks Challenge\n"
            "PROJECTS\nDAVE Hailo-8 Edge AI\n"
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

if __name__ == "__main__":
    unittest.main()

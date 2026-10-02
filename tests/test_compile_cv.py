import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "002-cv", "scripts")))
import compile_cv

class TestCompileCv(unittest.TestCase):
    def test_find_compiler_detection(self):
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/" + cmd if cmd == "pdflatex" else None
            compiler = compile_cv.detect_latex_compiler()
            self.assertEqual(compiler, "pdflatex")

    def test_find_compiler_none(self):
        with patch("shutil.which", return_value=None):
            compiler = compile_cv.detect_latex_compiler()
            self.assertIsNone(compiler)

    def test_build_compile_command(self):
        out_dir = Path("002-cv/dist")
        cmd = compile_cv.build_compile_command(
            compiler="pdflatex",
            tex_file=Path("002-cv/Diego_Perea_Resume.tex"),
            output_dir=out_dir
        )
        self.assertIn("pdflatex", cmd[0])
        expected_out = f"-output-directory={out_dir.resolve()}"
        self.assertEqual(cmd[3], expected_out)

    def test_build_compile_command_tectonic(self):
        out_dir = Path("002-cv/dist")
        cmd = compile_cv.build_compile_command(
            compiler="tectonic",
            tex_file=Path("002-cv/Diego_Perea_Resume.tex"),
            output_dir=out_dir
        )
        self.assertIn("tectonic", cmd[0])
        self.assertIn("--outdir", cmd)
        self.assertIn(str(out_dir.resolve()), cmd)

    @patch("compile_cv.pypdfium2")
    def test_generate_preview_png(self, mock_pdfium):
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_image = MagicMock()
        
        mock_pdfium.PdfDocument.return_value = mock_doc
        mock_doc.__len__.return_value = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_page.render.return_value.to_pil.return_value = mock_image
        
        pdf_path = Path("002-cv/dist/resume.pdf")
        png_path = compile_cv.generate_preview_image(pdf_path, dpi=150)
        
        self.assertEqual(png_path, pdf_path.with_suffix(".png"))
        mock_image.save.assert_called_once()

if __name__ == "__main__":
    unittest.main()

import os
import unittest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "002-cv", "scripts")))
import generate_resume_tex

class TestGenerateResumeTex(unittest.TestCase):
    def test_render_tex_template(self):
        template_content = r"""
\documentclass{article}
\begin{document}
\textbf{<<NAME>>} \\
<<LOCATION>> \textbullet\ <<EMAIL>> \textbullet\ <<PHONE>> \\
<<SCHOOL>> -- <<DEGREE>>
\end{document}
"""
        profile = {
            "name": "Alex Chen",
            "location": "Seattle, WA",
            "email": "alex@cs.washington.edu",
            "phone": "+1 206 555 0123",
            "school": "University of Washington",
            "degree": "B.S. in Computer Science"
        }
        rendered = generate_resume_tex.render_template_string(template_content, profile)
        self.assertIn("Alex Chen", rendered)
        self.assertIn("Seattle, WA", rendered)
        self.assertIn("alex@cs.washington.edu", rendered)
        self.assertIn("University of Washington", rendered)
        self.assertNotIn("<<NAME>>", rendered)

    def test_escape_latex_special_characters(self):
        raw_text = "Data Science & Mathematics (100% GPA)"
        escaped = generate_resume_tex.escape_latex(raw_text)
        self.assertEqual(escaped, r"Data Science \& Mathematics (100\% GPA)")

    def test_generate_resume_file(self):
        template_content = r"\textbf{<<NAME>>} - <<DEGREE>>"
        profile = {
            "name": "Alex Chen",
            "degree": "B.S. in Computer Science"
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            tpl_path = Path(tmpdir) / "template.tex"
            out_path = Path(tmpdir) / "output.tex"
            tpl_path.write_text(template_content, encoding="utf-8")
            
            result_path = generate_resume_tex.generate_resume(tpl_path, out_path, profile)
            self.assertTrue(result_path.exists())
            content = result_path.read_text(encoding="utf-8")
            self.assertIn("Alex Chen", content)
    def test_template_tex_rendering(self):
        template_file = Path(__file__).resolve().parent.parent / "002-cv" / "template.tex"
        self.assertTrue(template_file.exists())
        profile = {
            "name": "Candidate Name",
            "location": "City, Country",
            "email": "candidate@example.com",
            "phone": "+1 555 0100",
            "linkedin": "https://linkedin.com/in/candidate",
            "github": "https://github.com/candidate",
            "school": "University of Technology",
            "degree": "B.S. in Data Science & Mathematics",
            "graduation": "Aug 2024 -- May 2028 (Expected)"
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "Candidate_Resume.tex"
            generate_resume_tex.generate_resume(template_file, out_file, profile)
            self.assertTrue(out_file.exists())
            rendered = out_file.read_text(encoding="utf-8")
            self.assertIn("Candidate Name", rendered)
            self.assertIn("Data Science \\& Mathematics", rendered)
            self.assertNotIn("<<NAME>>", rendered)
            self.assertNotIn("<<DEGREE>>", rendered)
            self.assertNotIn("<<SCHOOL>>", rendered)

if __name__ == "__main__":

    unittest.main()

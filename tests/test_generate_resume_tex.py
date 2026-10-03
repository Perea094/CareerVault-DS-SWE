import os
import unittest
import tempfile
import json
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
            "graduation": "Aug 2024 -- May 2028 (Expected)",
            "gpa": "3.95/4.0",
            "distinctions": "First Class Honors"
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "Candidate_Resume.tex"
            generate_resume_tex.generate_resume(template_file, out_file, profile)
            self.assertTrue(out_file.exists())
            rendered = out_file.read_text(encoding="utf-8")
            self.assertIn("Candidate Name", rendered)
            self.assertIn("Data Science \\& Mathematics", rendered)
            self.assertIn("3.95/4.0", rendered)
            self.assertIn("First Class Honors", rendered)
            self.assertNotIn("<<NAME>>", rendered)
            self.assertNotIn("<<DEGREE>>", rendered)
            self.assertNotIn("<<SCHOOL>>", rendered)
            self.assertNotIn("<<GPA>>", rendered)

    def test_generate_from_markdown(self):
        sample_md = """---
type: custom-cv
candidate: "Elena Rostova"
---

# Elena Rostova

Zurich, Switzerland • elena@ethz.ch • +41 44 632 1111 • [LinkedIn](https://linkedin.com/in/elena) • [GitHub](https://github.com/elena)

---

## Education

**ETH Zurich** — Zurich, Switzerland  
B.S. in Computer Science — *2023 – 2026*  
GPA: 5.8/6.0  
**Selected Coursework:** Machine Learning, Algorithms & Data Structures

---

## Experience

**Robotics Systems Group** — Zurich, Switzerland  
**Research Intern** — *Jun 2025 – Aug 2025*  
- Designed real-time trajectory planners using C++ and ROS 2.
- Reduced path optimization latency by 35% using quadratic programming.

---

## Projects

**Distributed Drone Swarm** — *C++, Python, ZeroMQ* — *2025* • [GitHub](https://github.com/elena/drone-swarm)  
- Architected decentralized communication protocols for 16 simulated micro-drones.

---

## Technical Skills

**Programming Languages:** Python, C++, Rust, SQL  
**Tools & Systems:** Linux, Docker, ROS 2, Git  
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "resume.md"
            out_path = Path(tmpdir) / "resume.tex"
            md_path.write_text(sample_md, encoding="utf-8")

            result = generate_resume_tex.generate_from_markdown(md_path, out_path)
            self.assertTrue(result.exists())
            tex_content = result.read_text(encoding="utf-8")

            self.assertIn(r"\cvsection{Education}", tex_content)
            self.assertIn(r"\cvsection{Experience}", tex_content)
            self.assertIn(r"\cvsection{Projects}", tex_content)
            self.assertIn(r"\cvsection{Technical Skills}", tex_content)
            self.assertIn("Elena Rostova", tex_content)
            self.assertIn("ETH Zurich", tex_content)
            self.assertIn("Robotics Systems Group", tex_content)
            self.assertIn(r"\href{https://github.com/elena/drone-swarm}", tex_content)

    def test_generate_from_json_structured(self):
        sample_json = {
            "basics": {
                "name": "Marcus Vance",
                "location": "Austin, TX",
                "email": "marcus@utexas.edu",
                "phone": "+1 512 555 0188",
                "linkedin": "https://linkedin.com/in/marcusv",
                "github": "https://github.com/marcusv"
            },
            "education": [
                {
                    "institution": "University of Texas at Austin",
                    "degree": "B.S. in Electrical and Computer Engineering",
                    "graduation": "Dec 2026",
                    "gpa": "3.88/4.0",
                    "coursework": ["Operating Systems", "VLSI Design"]
                }
            ],
            "experience": [
                {
                    "company": "Silicon Edge Labs",
                    "role": "Firmware Engineer Intern",
                    "location": "Austin, TX",
                    "dates": "May 2025 – Aug 2025",
                    "bullets": [
                        "Optimized SPI peripheral drivers achieving 2x SPI bus throughput.",
                        "Implemented hardware ring buffers on ARM Cortex-M4."
                    ]
                }
            ],
            "projects": [
                {
                    "name": "RISC-V Microarchitecture",
                    "technologies": "SystemVerilog, Verilator, C++",
                    "dates": "2025",
                    "link": "https://github.com/marcusv/riscv-core",
                    "bullets": ["Designed 5-stage pipelined processor core."]
                }
            ],
            "skills": {
                "Languages": ["C", "C++", "Python", "SystemVerilog"],
                "Tools": ["Git", "GDB", "FreeRTOS", "Linux"]
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "resume.json"
            out_path = Path(tmpdir) / "resume.tex"
            json_path.write_text(json.dumps(sample_json), encoding="utf-8")

            result = generate_resume_tex.generate_from_json(json_path, out_path)
            self.assertTrue(result.exists())
            tex = result.read_text(encoding="utf-8")

            self.assertIn("Marcus Vance", tex)
            self.assertIn("University of Texas at Austin", tex)
            self.assertIn("Silicon Edge Labs", tex)
            self.assertIn("RISC-V Microarchitecture", tex)
            self.assertIn(r"\cvsection{Experience}", tex)

if __name__ == "__main__":
    unittest.main()

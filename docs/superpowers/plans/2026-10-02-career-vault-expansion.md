# Career Vault Expansion: Clean-Up, Automation Tooling, & Lifecycle Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the repository structure, implement automated CV compilation and ATS validation scripts with PDF/PNG generation, and add four end-to-end career lifecycle skills (`interview-prep`, `application-tracker`, `networking-outreach`, `cover-letter-writer`) with full unit test coverage.

**Architecture:** 
1. **Structural Cleanup**: Unify project directories, resolve git tracked/deleted files, and standardize relative paths across skills.
2. **Build Tooling (`002-cv/scripts/`)**: Standalone Python scripts for LaTeX compilation with auto-PNG preview generation via `pypdfium2` and ATS parseability scanning via `pdfplumber`.
3. **Career Lifecycle Skills (`.agents/skills/`)**: Modular skills equipped with automated CLI scripts that cross-reference verified background evidence in `001-background/` and opportunities in `004-work-opportunities/` to output Obsidian-compliant Markdown notes and update pipeline JSON databases.

**Tech Stack:** Python 3.11, `pytest`, `pdfplumber`, `pypdfium2`, `pillow`, LaTeX (`tectonic`/`pdflatex`), Git, Markdown/YAML.

---

### Task 1: Clean Up Directory Typo and Inconsistent Project Folders

**Files:**
- Move/Merge: `001-background/proyects/proyects-2026-09-15.md` $\to$ `001-background/projects/projects-2026-09-15.md`
- Remove: `001-background/proyects/`
- Modify: `001-background/findings/consolidated-findings.md` (update any references to `proyects/`)

- [ ] **Step 1: Check existing files in projects vs proyects**

Inspect:
```powershell
Get-ChildItem 001-background/projects, 001-background/proyects
```

- [ ] **Step 2: Rename and move `proyects-2026-09-15.md` to `001-background/projects/`**

Run:
```powershell
Move-Item -Path "001-background/proyects/proyects-2026-09-15.md" -Destination "001-background/projects/projects-2026-09-15.md"
Remove-Item -Path "001-background/proyects" -Recurse -Force
```

- [ ] **Step 3: Update references in `consolidated-findings.md`**

Replace occurrences of `001-background/proyects/` with `001-background/projects/` in `001-background/findings/consolidated-findings.md`.

- [ ] **Step 4: Verify directory structure**

Run:
```powershell
Test-Path "001-background/proyects"
Test-Path "001-background/projects/projects-2026-09-15.md"
```
Expected: `False` for `proyects`, `True` for `projects-2026-09-15.md`.

- [ ] **Step 5: Commit cleanup**

```bash
git add 001-background/
git commit -m "fix(vault): unify proyects into projects directory"
```

---

### Task 2: Standardize Absolute Paths in Skills to Vault-Relative Paths

**Files:**
- Modify: `.agents/skills/add-experience-curriculum/SKILL.md:10-15`

- [ ] **Step 1: Review current hardcoded path in `add-experience-curriculum/SKILL.md`**

Lines 10-15 hardcode `C:\Users\Diego Perea\Desktop\Curriculum`.

- [ ] **Step 2: Update path definition to support dynamic/relative resolution**

Modify `.agents/skills/add-experience-curriculum/SKILL.md` so that the target paths are documented relative to the vault root:
```markdown
## Target Vault Paths
The skill operates using paths relative to the vault root (or detected workspace root):
- **Vault Root:** `.` (Curriculum workspace root)
- **Experiences Directory:** `001-background/experiences/`
- **Consolidated Findings:** `001-background/findings/consolidated-findings.md`
```

- [ ] **Step 3: Verify no other SKILL.md files hardcode user paths**

Run:
```powershell
Get-ChildItem -Recurse -Filter "SKILL.md" | Select-String "C:\\Users\\"
```
Expected: Zero matches.

- [ ] **Step 4: Commit path standardization**

```bash
git add .agents/skills/add-experience-curriculum/SKILL.md
git commit -m "refactor(skills): use vault-relative paths in add-experience-curriculum"
```

---

### Task 3: Clean Up Git Tracking for Reorganized Vault Directories

**Files:**
- Git staging: Stage all moved folders (`001-background`, `002-cv`, `003-extra`, `004-work-opportunities`, `.agents`, `GEMINI.md`) and stage deletions of legacy un-numbered folders (`background`, `cv`, `extra`, `work-opportunities`, `handoff.md`).

- [ ] **Step 1: Review git status**

Run:
```powershell
git status -s
```

- [ ] **Step 2: Stage all changes including renames and deletions**

Run:
```powershell
git add -A
```

- [ ] **Step 3: Verify git status reflects clean renames**

Run:
```powershell
git status
```
Expected: Changes staged for commit showing renames (e.g. `renamed: cv/Diego_Perea_Resume.tex -> 002-cv/Diego_Perea_Resume.tex`), untracked files staged.

- [ ] **Step 4: Commit reorganization**

```bash
git commit -m "chore(vault): synchronize git tracking with numbered vault structure"
```

---

### Task 4: Automated CV Compiler (`002-cv/scripts/compile_cv.py`)

**Files:**
- Create: `002-cv/scripts/compile_cv.py`
- Test: `tests/test_compile_cv.py`

- [ ] **Step 1: Write failing test for CV compiler**

Create `tests/test_compile_cv.py`:
```python
import os
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module to be implemented
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
        cmd = compile_cv.build_compile_command(
            compiler="pdflatex",
            tex_file=Path("002-cv/Diego_Perea_Resume.tex"),
            output_dir=Path("002-cv/dist")
        )
        self.assertIn("pdflatex", cmd[0])
        self.assertIn("-output-directory", cmd)

    def test_build_compile_command_tectonic(self):
        cmd = compile_cv.build_compile_command(
            compiler="tectonic",
            tex_file=Path("002-cv/Diego_Perea_Resume.tex"),
            output_dir=Path("002-cv/dist")
        )
        self.assertIn("tectonic", cmd[0])
        self.assertIn("--outdir", cmd)

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
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_compile_cv.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'compile_cv'`.

- [ ] **Step 3: Implement `002-cv/scripts/compile_cv.py`**

Create `002-cv/scripts/compile_cv.py`:
```python
#!/usr/bin/env python3
"""
Automated LaTeX CV Compiler with High-Resolution PNG Preview Generation.
Detects available LaTeX compilers (tectonic, pdflatex, xelatex, latexmk),
compiles .tex resumes to PDF, and renders a page 1 PNG snapshot for Obsidian embedding.
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

try:
    import pypdfium2
except ImportError:
    pypdfium2 = None

SUPPORTED_COMPILERS = ["tectonic", "pdflatex", "xelatex", "latexmk"]

def detect_latex_compiler():
    """Detects first available LaTeX compiler in PATH."""
    for compiler in SUPPORTED_COMPILERS:
        if shutil.which(compiler):
            return compiler
    return None

def build_compile_command(compiler: str, tex_file: Path, output_dir: Path) -> list:
    """Builds appropriate CLI arguments for the detected compiler."""
    tex_path = str(tex_file.resolve())
    out_path = str(output_dir.resolve())
    
    if compiler == "tectonic":
        return [compiler, "--outdir", out_path, tex_path]
    elif compiler in ["pdflatex", "xelatex"]:
        return [
            compiler,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_path}",
            tex_path
        ]
    elif compiler == "latexmk":
        return [
            compiler,
            "-pdf",
            f"-outdir={out_path}",
            "-interaction=nonstopmode",
            tex_path
        ]
    else:
        raise ValueError(f"Unsupported compiler: {compiler}")

def generate_preview_image(pdf_path: Path, output_png: Path = None, dpi: int = 150) -> Path:
    """Renders the first page of the PDF to a high-resolution PNG using pypdfium2."""
    if pypdfium2 is None:
        raise RuntimeError("pypdfium2 is not installed. Install it with: pip install pypdfium2")
    
    if output_png is None:
        output_png = pdf_path.with_suffix(".png")
        
    doc = pypdfium2.PdfDocument(str(pdf_path))
    if len(doc) == 0:
        raise ValueError(f"PDF document {pdf_path} contains 0 pages.")
        
    page = doc[0]
    # Standard 72 DPI base scale * (dpi / 72)
    scale = dpi / 72.0
    image = page.render(scale=scale).to_pil()
    image.save(str(output_png), format="PNG")
    return output_png

def compile_resume(tex_file: Path, output_dir: Path = None, generate_png: bool = True, dpi: int = 150):
    """Orchestrates compilation and preview generation."""
    tex_file = Path(tex_file)
    if not tex_file.exists():
        raise FileNotFoundError(f"LaTeX file not found: {tex_file}")
        
    if output_dir is None:
        output_dir = tex_file.parent
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    compiler = detect_latex_compiler()
    if not compiler:
        raise RuntimeError(
            "No LaTeX compiler found in PATH. Please install Tectonic or MiKTeX.\n"
            "Quick install (PowerShell): winget install MiKTeX.MiKTeX"
        )
        
    cmd = build_compile_command(compiler, tex_file, output_dir)
    print(f"[INFO] Compiling {tex_file.name} using {compiler}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[ERROR] LaTeX compilation failed:\n{result.stderr or result.stdout}", file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd, output=result.stdout, stderr=result.stderr)
        
    pdf_name = tex_file.stem + ".pdf"
    pdf_path = output_dir / pdf_name
    print(f"[SUCCESS] PDF generated at: {pdf_path}")
    
    png_path = None
    if generate_png:
        try:
            png_path = generate_preview_image(pdf_path, dpi=dpi)
            print(f"[SUCCESS] PNG preview generated at: {png_path}")
        except Exception as e:
            print(f"[WARN] Failed to generate PNG preview: {e}", file=sys.stderr)
            
    return pdf_path, png_path

def main():
    parser = argparse.ArgumentParser(description="Compile LaTeX Resume to PDF and PNG preview")
    parser.add_argument("tex_file", nargs="?", default="002-cv/Diego_Perea_Resume.tex", help="Path to .tex file")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory to place PDF and PNG")
    parser.add_argument("--no-preview", action="store_true", help="Skip PNG preview generation")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for PNG preview (default: 150)")
    parser.add_argument("--preview-only", action="store_true", help="Only generate PNG from existing PDF")
    
    args = parser.parse_args()
    tex_path = Path(args.tex_file)
    
    if args.preview_only:
        pdf_path = tex_path.with_suffix(".pdf")
        if not pdf_path.exists():
            print(f"[ERROR] PDF not found: {pdf_path}", file=sys.stderr)
            sys.exit(1)
        png = generate_preview_image(pdf_path, dpi=args.dpi)
        print(f"[SUCCESS] Preview saved to: {png}")
        sys.exit(0)
        
    try:
        compile_resume(
            tex_file=tex_path,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            generate_png=not args.no_preview,
            dpi=args.dpi
        )
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_compile_cv.py
```
Expected: PASS (4 passed).

- [ ] **Step 5: Commit `compile_cv.py` and test**

```bash
git add 002-cv/scripts/compile_cv.py tests/test_compile_cv.py
git commit -m "feat(cv): add automated LaTeX CV compiler with pypdfium2 PNG preview generator"
```

---

### Task 5: ATS Resume Parseability Scanner (`002-cv/scripts/validate_ats.py`)

**Files:**
- Create: `002-cv/scripts/validate_ats.py`
- Test: `tests/test_validate_ats.py`

- [ ] **Step 1: Write failing test for ATS validator**

Create `tests/test_validate_ats.py`:
```python
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
            self.assertIn("Resume exceeds 1 page", result["warnings"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_validate_ats.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'validate_ats'`.

- [ ] **Step 3: Implement `002-cv/scripts/validate_ats.py`**

Create `002-cv/scripts/validate_ats.py`:
```python
#!/usr/bin/env python3
"""
ATS (Applicant Tracking System) Machine-Readability Scanner.
Audits compiled resume PDFs using pdfplumber to verify text extractability,
standard section headers, contact details, single-page constraint, and density.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

STANDARD_SECTIONS = {
    "education": [r"\beducation\b", r"\beducación\b", r"\bacademic\b"],
    "experience": [r"\bexperience\b", r"\bexperiencia\b", r"\bemployment\b", r"\bwork history\b"],
    "projects": [r"\bprojects\b", r"\bproyectos\b", r"\btechnical projects\b"],
    "skills": [r"\bskills\b", r"\bhabilidades\b", r"\btechnical skills\b", r"\btechnologies\b"]
}

def scan_pdf_for_ats(pdf_path: Path) -> dict:
    """Scans PDF for ATS parseability metrics and returns audit findings dictionary."""
    if pdfplumber is None:
        raise RuntimeError("pdfplumber is required. Install with: pip install pdfplumber")
        
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
    warnings = []
    sections_found = []
    full_text = ""
    
    with pdfplumber.open(str(pdf_path)) as pdf:
        page_count = len(pdf.pages)
        is_single_page = (page_count == 1)
        
        if not is_single_page:
            warnings.append(f"Resume exceeds 1 page (actual: {page_count} pages). High risk for intern/new grad roles.")
            
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            full_text += text + "\n"
            
    word_count = len(full_text.split())
    char_count = len(full_text)
    
    if word_count < 150:
        warnings.append(f"Resume text is suspiciously short ({word_count} words). Check for unextracted fonts or raster graphics.")
    elif word_count > 600:
        warnings.append(f"Resume text is very dense ({word_count} words). Ensure adequate whitespace for human reviewers.")

    # Contact info detection
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", full_text)
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", full_text)
    github_match = re.search(r"github\.com/[A-Za-z0-9_-]+", full_text, re.IGNORECASE)
    linkedin_match = re.search(r"linkedin\.com/in/[A-Za-z0-9_-]+", full_text, re.IGNORECASE)
    
    has_contact = {
        "email": bool(email_match),
        "phone": bool(phone_match),
        "github": bool(github_match),
        "linkedin": bool(linkedin_match)
    }
    
    if not has_contact["email"]:
        warnings.append("No email address detected by text parser.")
    if not has_contact["phone"]:
        warnings.append("No phone number detected by text parser.")
        
    # Standard sections detection
    text_lower = full_text.lower()
    for section_name, patterns in STANDARD_SECTIONS.items():
        found = any(re.search(pat, text_lower) for pat in patterns)
        if found:
            sections_found.append(section_name)
        else:
            warnings.append(f"Standard section missing: '{section_name.capitalize()}'")
            
    # Calculate ATS score (0 - 100)
    score = 100
    if not is_single_page:
        score -= 25
    if not has_contact["email"]:
        score -= 20
    if not has_contact["phone"]:
        score -= 10
    
    missing_sections = set(STANDARD_SECTIONS.keys()) - set(sections_found)
    score -= len(missing_sections) * 10
    if word_count < 150:
        score -= 20
        
    score = max(0, score)
    
    return {
        "pdf_path": str(pdf_path),
        "page_count": page_count,
        "is_single_page": is_single_page,
        "word_count": word_count,
        "char_count": char_count,
        "sections_found": sections_found,
        "missing_sections": list(missing_sections),
        "has_contact_info": has_contact,
        "warnings": warnings,
        "ats_score": score,
        "verdict": "ATS Ready" if score >= 85 else ("Borderline" if score >= 60 else "ATS Red Flag")
    }

def main():
    parser = argparse.ArgumentParser(description="Audit PDF Resume for ATS Parseability")
    parser.add_argument("pdf_path", help="Path to resume PDF file")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()
    
    try:
        report = scan_pdf_for_ats(Path(args.pdf_path))
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("==================================================")
            print(f"ATS AUDIT REPORT: {Path(args.pdf_path).name}")
            print(f"Score: {report['ats_score']}/100 ({report['verdict']})")
            print(f"Pages: {report['page_count']} | Words: {report['word_count']}")
            print("--------------------------------------------------")
            print("Contact Info:")
            for k, v in report['has_contact_info'].items():
                print(f"  - {k.capitalize()}: {'[PASS]' if v else '[MISSING]'}")
            print("Sections Detected:")
            for sec in STANDARD_SECTIONS.keys():
                status = "[PASS]" if sec in report['sections_found'] else "[MISSING]"
                print(f"  - {sec.capitalize()}: {status}")
            if report['warnings']:
                print("Warnings:")
                for w in report['warnings']:
                    print(f"  ! {w}")
            print("==================================================")
            
        sys.exit(0 if report["ats_score"] >= 70 else 1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_validate_ats.py
```
Expected: PASS (3 passed).

- [ ] **Step 5: Commit `validate_ats.py` and test**

```bash
git add 002-cv/scripts/validate_ats.py tests/test_validate_ats.py
git commit -m "feat(cv): add automated ATS parseability validator with pdfplumber"
```

---

### Task 6: GitHub Actions Workflow (`.github/workflows/ci.yml`)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

Create `.github/workflows/ci.yml`:
```yaml
name: CI & Opportunity Vault Tests

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    # Daily opportunity scout at 12:00 UTC (06:00 CDMX)
    - cron: '0 12 * * *'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pdfplumber pypdfium2 pillow requests beautifulsoup4

      - name: Run unit test suite
        run: |
          pytest tests/ -v

      - name: Run Opportunity Scanner Dry Run
        run: |
          python 004-work-opportunities/scripts/scan_opportunities.py
```

- [ ] **Step 2: Commit GitHub Actions workflow**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for test suite and daily opportunity scout"
```

---

### Task 7: Interview Prep Skill & Dossier Generator (`interview-prep`)

**Files:**
- Create: `.agents/skills/interview-prep/SKILL.md`
- Create: `.agents/skills/interview-prep/scripts/generate_dossier.py`
- Test: `tests/test_interview_prep.py`

- [ ] **Step 1: Write failing test for interview prep dossier generator**

Create `tests/test_interview_prep.py`:
```python
import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "interview-prep", "scripts")))
import generate_dossier

class TestInterviewPrep(unittest.TestCase):
    def test_format_star_story(self):
        story = generate_dossier.format_star_story(
            title="DAVE Edge AI System",
            situation="Wanted to detect safety violations on campus without cloud latency.",
            task="Architect a real-time edge processing pipeline on limited compute.",
            action="Deployed Hailo-8 NPU on Raspberry Pi 5 with MediaPipe and custom OpenCV buffers.",
            result="Achieved 30 FPS inference with <50ms latency and won 1st place Expo Ingenierías."
        )
        self.assertIn("### DAVE Edge AI System", story)
        self.assertIn("**Situation:**", story)
        self.assertIn("**Task:**", story)
        self.assertIn("**Action:**", story)
        self.assertIn("**Result:**", story)

    def test_generate_interview_dossier_content(self):
        role_info = {
            "company": "Mistral AI",
            "role": "AI Research Engineer Intern",
            "tech_stack": ["PyTorch", "vLLM", "C++", "CUDA"]
        }
        background_assets = [
            {
                "title": "Ape-X DQN Street Fighter II",
                "metrics": "3,700 FPS on distributed actors",
                "star": {
                    "s": "Need high throughput RL.",
                    "t": "Scale distributed experience replay.",
                    "a": "Implemented custom vectorized environments.",
                    "r": "Reached 3,700 FPS and 85% win rate."
                }
            }
        ]
        markdown = generate_dossier.build_dossier_markdown(role_info, background_assets)
        self.assertIn("# Interview Preparation Dossier: Mistral AI", markdown)
        self.assertIn("Ape-X DQN Street Fighter II", markdown)
        self.assertIn("## Technical Question Bank", markdown)
        self.assertIn("## Behavioral STAR Grid", markdown)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_interview_prep.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'generate_dossier'`.

- [ ] **Step 3: Implement `generate_dossier.py`**

Create `.agents/skills/interview-prep/scripts/generate_dossier.py`:
```python
#!/usr/bin/env python3
"""
Generates targeted interview preparation dossiers with STAR behavioral stories,
technical question drills, and system design talking points grounded in vault evidence.
"""

from typing import Dict, List, Any

def format_star_story(title: str, situation: str, task: str, action: str, result: str) -> str:
    """Formats a structured STAR behavioral story in Markdown."""
    return f"""### {title}
- **Situation:** {situation}
- **Task:** {task}
- **Action:** {action}
- **Result:** {result}
"""

def build_dossier_markdown(role_info: Dict[str, Any], background_assets: List[Dict[str, Any]]) -> str:
    """Builds a complete Markdown interview dossier for an opportunity."""
    company = role_info.get("company", "Target Company")
    role = role_info.get("role", "Target Role")
    tech_stack = ", ".join(role_info.get("tech_stack", []))
    
    star_sections = ""
    for asset in background_assets:
        star = asset.get("star", {})
        star_sections += format_star_story(
            title=asset.get("title", "Project"),
            situation=star.get("s", "Context"),
            task=star.get("t", "Challenge"),
            action=star.get("a", "Implementation"),
            result=star.get("r", "Measurable Impact")
        ) + "\n"

    return f"""---
created: 2026-10-02
type: interview-dossier
company: "{company}"
role: "{role}"
status: active
tags: [interview-prep, technical-interview, star-method]
---

# Interview Preparation Dossier: {company} — {role}

## 1. Company & Role Intelligence
- **Target Company:** {company}
- **Role:** {role}
- **Core Technologies:** {tech_stack or "General Software / AI"}

---

## 2. Behavioral STAR Grid (Grounded in Verified Background)
{star_sections}
---

## 3. Technical Question Bank & Architectural Drills
### Core Technical Competencies
- Explain trade-offs in distributed systems / high-throughput inference pipelines.
- Deep dive into concurrency, memory management, and GPU/NPU hardware acceleration.
- Describe how you handle model evaluation, hallucinations, or covariate drift.

### 5 Questions to Ask the Interviewer (Reverse Screen)
1. "What does the deployment and validation lifecycle look like for models transitioning from experimentation to production here?"
2. "What are the most challenging latency or throughput bottlenecks the team is currently untangling?"
3. "How does engineering collaborate with product when prioritizing reliability over new feature velocity?"
4. "What is the expected scope of ownership for an intern on this team during the first 6 weeks?"
5. "What distinguishes the top 5% of performers who have gone through this group?"
"""
```

- [ ] **Step 4: Implement `.agents/skills/interview-prep/SKILL.md`**

Create `.agents/skills/interview-prep/SKILL.md`:
```markdown
---
name: interview-prep
description: Prepare candidates for technical, behavioral, and architectural interviews for any opportunity in 004-work-opportunities/ or user-provided job posting using STAR stories grounded in 001-background/.
---

# interview-prep

Generates structured, company-specific technical interview dossiers and conducts interactive mock interviews in the chat.

## When to Use
- Preparing for an upcoming initial screen, technical round, or hiring manager interview.
- Translating verified projects in `001-background/` into concise STAR (Situation, Task, Action, Result) answers.
- Running interactive mock interview drills where the agent poses challenging questions, waits for user answers, and provides scoring and feedback.

## Workflow
1. Read the target opportunity description in `004-work-opportunities/` or prompt input.
2. Cross-reference `001-background/experiences/` and `001-background/projects/` for matching technical proof points.
3. Generate dossier note under `004-work-opportunities/dossiers/YYYY-MM-DD-<company>-prep.md`.
4. Run interactive mock interview session in chat upon user request.
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_interview_prep.py
```
Expected: PASS (2 passed).

- [ ] **Step 6: Commit interview prep skill**

```bash
git add .agents/skills/interview-prep/ tests/test_interview_prep.py
git commit -m "feat(skills): add interview-prep skill and dossier generation engine"
```

---

### Task 8: Application Tracker Skill & Pipeline Engine (`application-tracker`)

**Files:**
- Create: `.agents/skills/application-tracker/SKILL.md`
- Create: `.agents/skills/application-tracker/scripts/track_application.py`
- Test: `tests/test_application_tracker.py`

- [ ] **Step 1: Write failing test for application tracker**

Create `tests/test_application_tracker.py`:
```python
import os
import unittest
import json
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "application-tracker", "scripts")))
import track_application

class TestApplicationTracker(unittest.TestCase):
    def test_valid_statuses(self):
        self.assertIn("wishlist", track_application.VALID_STATUSES)
        self.assertIn("applied", track_application.VALID_STATUSES)
        self.assertIn("interview", track_application.VALID_STATUSES)
        self.assertIn("offer", track_application.VALID_STATUSES)
        self.assertIn("rejected", track_application.VALID_STATUSES)

    def test_update_application_status(self):
        data = {
            "opportunities": [
                {"id": "opp-1", "company": "Figma", "status": "eligible", "pipeline_status": "wishlist"}
            ]
        }
        updated = track_application.update_opportunity_pipeline(
            data,
            opp_id="opp-1",
            new_status="applied",
            date_applied="2026-10-02",
            notes="Applied via portal with tailored CV"
        )
        opp = updated["opportunities"][0]
        self.assertEqual(opp["pipeline_status"], "applied")
        self.assertEqual(opp["date_applied"], "2026-10-02")
        self.assertEqual(opp["pipeline_notes"], "Applied via portal with tailored CV")

    def test_generate_kanban_markdown(self):
        opportunities = [
            {"company": "Figma", "role": "Data Scientist", "pipeline_status": "applied", "apply_url": "https://figma.com"},
            {"company": "Google", "role": "SWE Intern", "pipeline_status": "interview", "apply_url": "https://google.com"}
        ]
        md = track_application.generate_pipeline_dashboard(opportunities)
        self.assertIn("# Application Pipeline Dashboard", md)
        self.assertIn("## Applied", md)
        self.assertIn("## Interview", md)
        self.assertIn("Figma", md)
        self.assertIn("Google", md)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_application_tracker.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'track_application'`.

- [ ] **Step 3: Implement `track_application.py`**

Create `.agents/skills/application-tracker/scripts/track_application.py`:
```python
#!/usr/bin/env python3
"""
Application Pipeline Tracker.
Manages application lifecycle progression (wishlist -> applied -> oa -> interview -> offer/rejected),
updates opportunities.json, and generates Obsidian Dataview/Kanban dashboards.
"""

from typing import Dict, List, Any

VALID_STATUSES = [
    "wishlist",
    "applied",
    "oa_received",
    "screening",
    "interview",
    "offer",
    "rejected",
    "withdrawn"
]

def update_opportunity_pipeline(
    db: Dict[str, Any],
    opp_id: str,
    new_status: str,
    date_applied: str = None,
    notes: str = None
) -> Dict[str, Any]:
    """Updates the pipeline status and metadata for a specific opportunity."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {VALID_STATUSES}")
        
    found = False
    for opp in db.get("opportunities", []):
        if opp.get("id") == opp_id or opp.get("company", "").lower() == opp_id.lower():
            opp["pipeline_status"] = new_status
            if date_applied:
                opp["date_applied"] = date_applied
            if notes:
                opp["pipeline_notes"] = notes
            found = True
            break
            
    if not found:
        raise KeyError(f"Opportunity with ID or Company '{opp_id}' not found in database.")
        
    return db

def generate_pipeline_dashboard(opportunities: List[Dict[str, Any]]) -> str:
    """Generates an Obsidian Kanban and summary dashboard."""
    grouped: Dict[str, List[Dict[str, Any]]] = {status: [] for status in VALID_STATUSES}
    
    for opp in opportunities:
        st = opp.get("pipeline_status", "wishlist")
        if st in grouped:
            grouped[st].append(opp)
        else:
            grouped["wishlist"].append(opp)
            
    md = """---
created: 2026-10-02
type: pipeline-dashboard
tags: [pipeline, kanban, applications]
---

# Application Pipeline Dashboard

"""
    for status in VALID_STATUSES:
        title = status.replace("_", " ").title()
        md += f"## {title}\n"
        items = grouped[status]
        if not items:
            md += "- *No applications in this stage*\n\n"
        else:
            for item in items:
                comp = item.get("company", "Unknown")
                role = item.get("role", "Unknown")
                url = item.get("apply_url", "#")
                date = item.get("date_applied", "")
                date_str = f" | Applied: {date}" if date else ""
                md += f"- [ ] **[{comp}]({url})** — {role}{date_str}\n"
            md += "\n"
            
    return md
```

- [ ] **Step 4: Implement `.agents/skills/application-tracker/SKILL.md`**

Create `.agents/skills/application-tracker/SKILL.md`:
```markdown
---
name: application-tracker
description: Track and update job application lifecycle stages (wishlist, applied, OA, interview, offer, rejected) across 004-work-opportunities/ and generate Obsidian Kanban pipeline boards.
---

# application-tracker

Maintains status tracking across active job submissions, logging application dates, custom CV versions used, and recruiter communication.

## When to Use
- When applying to a job posting in `004-work-opportunities/`.
- When receiving an Online Assessment (OA), interview invitation, or decision.
- Generating or updating the master `004-work-opportunities/application-pipeline.md` dashboard.
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_application_tracker.py
```
Expected: PASS (3 passed).

- [ ] **Step 6: Commit application tracker skill**

```bash
git add .agents/skills/application-tracker/ tests/test_application_tracker.py
git commit -m "feat(skills): add application-tracker skill and pipeline dashboard generator"
```

---

### Task 9: Networking Outreach Generator Skill (`networking-outreach`)

**Files:**
- Create: `.agents/skills/networking-outreach/SKILL.md`
- Create: `.agents/skills/networking-outreach/scripts/generate_outreach.py`
- Test: `tests/test_networking_outreach.py`

- [ ] **Step 1: Write failing test for networking outreach generator**

Create `tests/test_networking_outreach.py`:
```python
import os
import unittest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "networking-outreach", "scripts")))
import generate_outreach

class TestNetworkingOutreach(unittest.TestCase):
    def test_generate_three_tiers(self):
        role_info = {
            "company": "Databricks",
            "role": "Data Systems Intern",
            "key_skill": "Lakehouse & Spark Optimization"
        }
        candidate_info = {
            "name": "Diego Perea León",
            "school": "Tecnológico de Monterrey",
            "highlight": "Achieved 3,700 FPS distributed RL training pipeline"
        }
        
        outreach = generate_outreach.build_outreach_templates(role_info, candidate_info)
        
        self.assertIn("alumni", outreach)
        self.assertIn("recruiter", outreach)
        self.assertIn("hiring_manager", outreach)
        
        self.assertIn("Tecnológico de Monterrey", outreach["alumni"])
        self.assertIn("Databricks", outreach["recruiter"])
        self.assertIn("3,700 FPS", outreach["hiring_manager"])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_networking_outreach.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'generate_outreach'`.

- [ ] **Step 3: Implement `generate_outreach.py`**

Create `.agents/skills/networking-outreach/scripts/generate_outreach.py`:
```python
#!/usr/bin/env python3
"""
Generates 3-tiered high-conversion networking outreach messages (Alumni, Recruiter, Hiring Manager)
linking job requirements to verified background metrics.
"""

from typing import Dict, Any

def build_outreach_templates(role_info: Dict[str, Any], candidate_info: Dict[str, Any]) -> Dict[str, str]:
    """Builds personalized 3-tier networking messages."""
    company = role_info.get("company", "Target Company")
    role = role_info.get("role", "Target Role")
    name = candidate_info.get("name", "Candidate")
    school = candidate_info.get("school", "University")
    highlight = candidate_info.get("highlight", "verified engineering impact")

    alumni_msg = f"""Hi [First Name],

I noticed you're currently working at {company} and also graduated from {school}! I'm a student at {school} studying Data Science & Mathematics, following {company}'s recent work closely.

I recently submitted an application for the {role} position. Given your experience on the team, I would love to ask 2 quick questions about your journey and team culture if you ever have 10 minutes for a virtual coffee.

Thanks so much for your time!
Best,
{name}"""

    recruiter_msg = f"""Hi [First Name],

I hope you're having a great week! I recently applied for the {role} opening at {company}.

My technical background is focused on high-throughput systems and applied AI — recently, I {highlight}. Given {company}'s focus on engineering excellence, I'm confident my background aligns well with the team's needs.

I would love to connect and ensure my application is in front of the right hiring group.

Best regards,
{name}"""

    hiring_manager_msg = f"""Hi [First Name],

I've been following your team's engineering work at {company}, particularly around scalable infrastructure.

I'm applying for the {role} position. In my recent work, I {highlight}, solving bottlenecks around latency and throughput. I'd love to share brief technical notes on how I'd approach similar architecture challenges at {company}.

Would you be open to a brief 5-minute chat?

Best,
{name}"""

    return {
        "alumni": alumni_msg,
        "recruiter": recruiter_msg,
        "hiring_manager": hiring_manager_msg
    }
```

- [ ] **Step 4: Implement `.agents/skills/networking-outreach/SKILL.md`**

Create `.agents/skills/networking-outreach/SKILL.md`:
```markdown
---
name: networking-outreach
description: Generate high-conversion, personalized 3-tiered networking messages (Alumni, Technical Recruiter, Hiring Manager) for opportunities in 004-work-opportunities/ linking target requirements to candidate metrics.
---

# networking-outreach

Generates tailored outreach messages for LinkedIn or email to secure referrals and recruiter visibility for target job postings.

## When to Use
- After applying or bookmarking an opportunity in `004-work-opportunities/`.
- Seeking warm referrals from university alumni at the company.
- Direct messaging recruiters or engineering managers.
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_networking_outreach.py
```
Expected: PASS (1 passed).

- [ ] **Step 6: Commit networking outreach skill**

```bash
git add .agents/skills/networking-outreach/ tests/test_networking_outreach.py
git commit -m "feat(skills): add networking-outreach skill for 3-tier referral generation"
```

---

### Task 10: Cover Letter Writer Skill (`cover-letter-writer`)

**Files:**
- Create: `.agents/skills/cover-letter-writer/SKILL.md`

- [ ] **Step 1: Implement `.agents/skills/cover-letter-writer/SKILL.md`**

Create `.agents/skills/cover-letter-writer/SKILL.md`:
```markdown
---
name: cover-letter-writer
description: Generate concise, impact-driven, ATS-compliant 1-page cover letters and supplemental application essay responses strictly grounded in 001-background/ evidence.
---

# cover-letter-writer

Creates customized, non-cliché 1-page cover letters and short supplemental essay responses for high-tier internship and new-grad job applications.

## Rules & Philosophy
1. **Zero Hallucination:** Every claim, framework, and metric MUST be grounded in `001-background/`.
2. **The 3-Paragraph Formula:**
   - **Paragraph 1 (Hook & Value Alignment):** State the exact role, company team, and 1 specific reason why the company's technical mission resonates.
   - **Paragraph 2 (Deep Technical Proof):** Deep dive into 1 or 2 relevant projects applying Google XYZ (*Accomplished [X], measured by [Y], by doing [Z]*), highlighting architectural ownership.
   - **Paragraph 3 (Forward Look & Logistics):** Address schedule alignment (e.g. 20–30h during semester, full-time summer), work authorization/entity details, and clear call-to-action.
3. **Format:** Output to `002-cv/Custom/YYYY-MM-DD-<company>-cover-letter.md`.
```

- [ ] **Step 2: Commit cover-letter-writer skill**

```bash
git add .agents/skills/cover-letter-writer/SKILL.md
git commit -m "feat(skills): add cover-letter-writer skill for grounded supplemental letters"
```

---

### Task 11: Final Integration & Comprehensive Test Verification

**Files:**
- Run all tests across `tests/`
- Verify git status is clean

- [ ] **Step 1: Run the full test suite**

Run:
```powershell
py -3.11 -m pytest tests/ -v
```
Expected: All tests pass (existing 20 tests + ~11 new tests = 31+ passing tests).

- [ ] **Step 2: Verify all skills are recognized**

Run:
```powershell
Get-ChildItem -Directory .agents/skills | Select-Object Name
```
Expected: Lists all 11 skills (`add-experience-curriculum`, `application-tracker`, `cover-letter-writer`, `expert-recruiter`, `interview-prep`, `markitdown`, `networking-outreach`, `obsidian-cli`, `opportunity-scout`, `preference-manager`, `tailored-cv`).

- [ ] **Step 3: Final Git status check**

Run:
```powershell
git status
```
Expected: Clean working tree.

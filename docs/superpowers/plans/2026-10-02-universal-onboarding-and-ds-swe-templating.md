# Universal Onboarding & DS/SWE Career Vault Templating Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a clean, modular onboarding engine (`setup_vault.py`), dynamic candidate profile extraction, and customizable resume templating optimized for Data Science and Software Engineering (SWE) students and engineers, making the repository effortlessly shareable with friends and GitHub without losing its rigor.

**Architecture:** 
1. **Dynamic Candidate Profile Layer (`001-background/candidate_profile.py`)**: Centralizes candidate identity extraction from `preferences.json` so skills dynamically populate candidate details instead of relying on hardcoded strings.
2. **Dynamic LaTeX Resume Templating (`002-cv/scripts/generate_resume_tex.py`)**: Ingests an ATS-compliant template with standard Jinja/brace-style placeholders and renders customized `.tex` files.
3. **Interactive Setup Wizard (`setup_vault.py`)**: Single-entry point CLI onboarding script that configures personal preferences, generates customized templates, and optionally ingests historical CVs via `markitdown`.
4. **Starter Blueprints & Root Documentation (`README.md` & `001-background/templates/`)**: Open-source documentation and DS/SWE project templates enforcing Google XYZ and STAR metrics.

**Tech Stack:** Python 3.11, `pytest`, Jinja2/string substitution, LaTeX, Markdown/YAML, Git.

---

### Task 1: Dynamic Candidate Profile Extraction (`001-background/candidate_profile.py`)

**Files:**
- Create: `001-background/candidate_profile.py`
- Test: `tests/test_candidate_profile.py`

- [ ] **Step 1: Write failing test for candidate profile loader**

Create `tests/test_candidate_profile.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_candidate_profile.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'candidate_profile'`.

- [ ] **Step 3: Implement `001-background/candidate_profile.py`**

Create `001-background/candidate_profile.py`:
```python
#!/usr/bin/env python3
"""
Dynamic Candidate Profile Loader.
Extracts candidate information, university background, contact links,
and career target domains from preferences.json with safe defaults for DS & SWE profiles.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union

DEFAULT_PROFILE = {
    "name": "Candidate",
    "school": "University",
    "degree": "B.S. in Computer Science / Data Science",
    "graduation": "Expected May 2027",
    "location": "City, Country",
    "work_authorization": "Needs Sponsorship / International",
    "email": "candidate@example.com",
    "phone": "+1 555 0100",
    "linkedin": "https://linkedin.com/in/username",
    "github": "https://github.com/username",
    "target_domains": ["Software Engineering", "Machine Learning", "Data Systems"],
    "compensation_floor": 20.0
}

def load_profile(preferences_path: Union[str, Path] = None) -> Dict[str, Any]:
    """Loads candidate profile from preferences.json with sensible fallbacks."""
    if preferences_path is None:
        preferences_path = Path(__file__).resolve().parent / "preferences.json"
    else:
        preferences_path = Path(preferences_path)
        
    if not preferences_path.exists():
        return dict(DEFAULT_PROFILE)
        
    try:
        with open(preferences_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return dict(DEFAULT_PROFILE)
        
    cand = data.get("candidate", {})
    goals = data.get("career_goals", {})
    comp = data.get("compensation", {})
    
    profile = {
        "name": cand.get("name") or DEFAULT_PROFILE["name"],
        "school": cand.get("school") or DEFAULT_PROFILE["school"],
        "degree": cand.get("degree") or DEFAULT_PROFILE["degree"],
        "graduation": cand.get("graduation") or DEFAULT_PROFILE["graduation"],
        "location": cand.get("location") or DEFAULT_PROFILE["location"],
        "work_authorization": cand.get("work_authorization") or DEFAULT_PROFILE["work_authorization"],
        "email": cand.get("email") or DEFAULT_PROFILE["email"],
        "phone": cand.get("phone") or DEFAULT_PROFILE["phone"],
        "linkedin": cand.get("linkedin") or DEFAULT_PROFILE["linkedin"],
        "github": cand.get("github") or DEFAULT_PROFILE["github"],
        "target_domains": goals.get("target_domains") or DEFAULT_PROFILE["target_domains"],
        "compensation_floor": comp.get("minimum_hourly_usd", DEFAULT_PROFILE["compensation_floor"])
    }
    return profile
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_candidate_profile.py
```
Expected: PASS (2 passed).

- [ ] **Step 5: Commit profile loader**

```bash
git add 001-background/candidate_profile.py tests/test_candidate_profile.py
git commit -m "feat(background): add dynamic candidate profile extraction layer"
```

---

### Task 2: Connect Skills to Dynamic Candidate Profile

**Files:**
- Modify: `.agents/skills/networking-outreach/scripts/generate_outreach.py`
- Modify: `.agents/skills/interview-prep/scripts/generate_dossier.py`
- Test: `tests/test_networking_outreach.py`
- Test: `tests/test_interview_prep.py`

- [ ] **Step 1: Update `generate_outreach.py` to auto-load candidate profile**

In `.agents/skills/networking-outreach/scripts/generate_outreach.py`, add support for auto-loading candidate info if omitted or empty:
```python
import os
import sys
from pathlib import Path

# Add 001-background to path to import candidate_profile
BACKGROUND_DIR = Path(__file__).resolve().parent.parent.parent.parent / "001-background"
if str(BACKGROUND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKGROUND_DIR))

try:
    import candidate_profile
except ImportError:
    candidate_profile = None

def get_default_candidate_info() -> dict:
    if candidate_profile:
        profile = candidate_profile.load_profile()
        return {
            "name": profile.get("name", "Candidate"),
            "school": profile.get("school", "University"),
            "highlight": "delivered high-throughput distributed systems & ML pipelines"
        }
    return {
        "name": "Candidate",
        "school": "University",
        "highlight": "delivered high-throughput distributed systems & ML pipelines"
    }
```
Update `build_outreach_templates(role_info: Dict[str, Any], candidate_info: Dict[str, Any] = None)`:
```python
    if not candidate_info:
        candidate_info = get_default_candidate_info()
```

- [ ] **Step 2: Update `generate_dossier.py` to include dynamic candidate signature**

In `.agents/skills/interview-prep/scripts/generate_dossier.py`, dynamically query candidate info for reverse questions and profile context:
```python
def build_dossier_markdown(role_info: Dict[str, Any], background_assets: List[Dict[str, Any]], candidate_name: str = None) -> str:
```
Default to `candidate_profile.load_profile().get("name")` if `candidate_name` is None.

- [ ] **Step 3: Run pytest on updated skills**

Run:
```powershell
py -3.11 -m pytest tests/test_networking_outreach.py tests/test_interview_prep.py -v
```
Expected: PASS (5 passed).

- [ ] **Step 4: Commit dynamic skill integration**

```bash
git add .agents/skills/networking-outreach/scripts/generate_outreach.py .agents/skills/interview-prep/scripts/generate_dossier.py
git commit -m "refactor(skills): connect outreach and interview prep to dynamic candidate profile"
```

---

### Task 3: Dynamic LaTeX Resume Generator (`002-cv/scripts/generate_resume_tex.py`)

**Files:**
- Create: `002-cv/scripts/generate_resume_tex.py`
- Create: `002-cv/template.tex` (standard placeholder template)
- Test: `tests/test_generate_resume_tex.py`

- [ ] **Step 1: Write failing test for resume generator**

Create `tests/test_generate_resume_tex.py`:
```python
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

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_generate_resume_tex.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'generate_resume_tex'`.

- [ ] **Step 3: Implement `002-cv/scripts/generate_resume_tex.py`**

Create `002-cv/scripts/generate_resume_tex.py`:
```python
#!/usr/bin/env python3
"""
Dynamic LaTeX Resume Generator.
Renders ATS-compliant LaTeX resumes by injecting candidate profile metadata into templates.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Any

LATEX_REPLACEMENTS = [
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
]

def escape_latex(text: str) -> str:
    """Escapes common LaTeX special characters in user input."""
    for raw, esc in LATEX_REPLACEMENTS:
        # Avoid double-escaping if already escaped
        text = re.sub(r"(?<!\\)" + re.escape(raw), esc, text)
    return text

def render_template_string(template_str: str, profile: Dict[str, Any]) -> str:
    """Replaces <<PLACEHOLDER>> markers with candidate profile values."""
    placeholders = {
        "<<NAME>>": escape_latex(profile.get("name", "Candidate")),
        "<<LOCATION>>": escape_latex(profile.get("location", "City, Country")),
        "<<EMAIL>>": escape_latex(profile.get("email", "candidate@example.com")),
        "<<PHONE>>": escape_latex(profile.get("phone", "+1 555 0100")),
        "<<LINKEDIN>>": profile.get("linkedin", ""),
        "<<GITHUB>>": profile.get("github", ""),
        "<<SCHOOL>>": escape_latex(profile.get("school", "University")),
        "<<DEGREE>>": escape_latex(profile.get("degree", "B.S. in Computer Science / Data Science")),
        "<<GRADUATION>>": escape_latex(profile.get("graduation", "May 2027")),
    }
    
    rendered = template_str
    for tag, val in placeholders.items():
        rendered = rendered.replace(tag, str(val))
    return rendered

def generate_resume(template_path: Path, output_path: Path, profile: Dict[str, Any]) -> Path:
    """Renders resume template to output .tex path."""
    template_path = Path(template_path)
    output_path = Path(output_path)
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
        
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        
    rendered = render_template_string(template_content, profile)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)
        
    return output_path
```

- [ ] **Step 4: Create standardized `002-cv/template.tex` with placeholders**

Update `002-cv/template.tex`:
```latex
\documentclass[10pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage{mathptmx}
\usepackage{geometry}
\geometry{letterpaper, left=0.4in, right=0.4in, top=0.35in, bottom=0.35in, nohead, nofoot}
\usepackage{hyperref}
\hypersetup{colorlinks=true, linkcolor=black, urlcolor=blue}
\usepackage{enumitem}
\setlist[itemize]{leftmargin=11pt, label={\small$\bullet$}, itemsep=0.5pt, topsep=1pt, parsep=0pt, partopsep=0pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\pagestyle{empty}

\newcommand{\cvsection}[1]{%
  \vspace{3.5pt}%
  {\small\textbf{\MakeUppercase{#1}}}\\[-3.5pt]%
  \rule{\textwidth}{0.4pt}\par\vspace{2pt}%
}

\begin{document}

\begin{center}
    {\LARGE \textbf{<<NAME>>}}\\[2pt]
    \small <<LOCATION>> \textbullet\ \href{mailto:<<EMAIL>>}{<<EMAIL>>} \textbullet\ <<PHONE>> \textbullet\ \href{<<LINKEDIN>>}{LinkedIn} \textbullet\ \href{<<GITHUB>>}{GitHub}
\end{center}
\vspace{-6pt}

\cvsection{Education}
\textbf{<<SCHOOL>>} \hfill <<LOCATION>>\\
\textit{<<DEGREE>>} \hfill <<GRADUATION>>\\
\textbf{Relevant Coursework:} Data Structures \& Algorithms, Machine Learning, Systems Programming, Distributed Systems, Database Management Systems

\cvsection{Technical Skills}
\textbf{Languages:} Python, C++, SQL, TypeScript, Bash\\
\textbf{Frameworks \& Libraries:} PyTorch, Hugging Face, vLLM, FastAPI, Docker, Git\\
\textbf{Data \& Cloud:} PostgreSQL, Databricks, Spark, AWS / GCP, Linux

\cvsection{Experience}
\textbf{Company / Project Organization} \hfill Location\\
\textit{Software Engineer / Data Science Intern} \hfill Month YYYY – Month YYYY
\begin{itemize}
    \item Engineered [high-impact pipeline/model], reducing latency by 35\% and improving throughput across 10k+ daily queries.
    \item Designed and deployed automated microservices using FastAPI and Docker with 99.8\% uptime.
\end{itemize}

\cvsection{Projects}
\textbf{Distributed AI Inference Engine} \textbullet\ \textit{Python, C++, CUDA, vLLM} \hfill Month YYYY
\begin{itemize}
    \item Architected high-throughput batching server delivering 3,000+ tokens/sec across multi-GPU nodes.
    \item Implemented custom KV-cache eviction policies, decreasing peak memory consumption by 22\%.
\end{itemize}

\end{document}
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_generate_resume_tex.py
```
Expected: PASS (2 passed).

- [ ] **Step 6: Commit resume generator**

```bash
git add 002-cv/scripts/generate_resume_tex.py 002-cv/template.tex tests/test_generate_resume_tex.py
git commit -m "feat(cv): add dynamic LaTeX resume generator with template placeholders"
```

---

### Task 4: Interactive Setup Wizard (`setup_vault.py`)

**Files:**
- Create: `setup_vault.py`
- Test: `tests/test_setup_vault.py`

- [ ] **Step 1: Write failing test for setup wizard**

Create `tests/test_setup_vault.py`:
```python
import os
import unittest
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
            
            # Put dummy template.tex
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

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
py -3.11 -m pytest tests/test_setup_vault.py
```
Expected: FAIL with `ModuleNotFoundError: No module named 'setup_vault'`.

- [ ] **Step 3: Implement `setup_vault.py`**

Create `setup_vault.py`:
```python
#!/usr/bin/env python3
"""
Career Vault Onboarding & Setup Wizard.
Initializes and personalizes the Career Vault for Data Science and Software Engineering candidates.
Configures 001-background/preferences.json, syncs preferences.md, and generates a personalized LaTeX CV.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "002-cv", "scripts")))
try:
    import generate_resume_tex
except ImportError:
    generate_resume_tex = None

DEFAULT_AVAILABILITY_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DEFAULT_SLOTS = [
    "06_00", "06_30", "07_00", "07_30", "08_00", "08_30", "09_00", "09_30",
    "10_00", "10_30", "11_00", "11_30", "12_00", "12_30", "13_00", "13_30",
    "14_00", "14_30", "15_00", "15_30", "16_00", "16_30", "17_00", "17_30",
    "18_00", "18_30", "19_00", "19_30", "20_00", "20_30", "21_00", "21_30"
]

def build_default_schedule() -> Dict[str, Dict[str, str]]:
    grid = {}
    for day in DEFAULT_AVAILABILITY_DAYS:
        grid[day] = {slot: "available" if "09_00" <= slot <= "17_00" else "busy" for slot in DEFAULT_SLOTS}
    return grid

def configure_vault(vault_dir: Path, profile: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Configures the vault preferences, Markdown sync, and starter LaTeX CV."""
    vault_dir = Path(vault_dir)
    bg_dir = vault_dir / "001-background"
    cv_dir = vault_dir / "002-cv"
    
    if dry_run:
        return {"success": True, "dry_run": True, "profile": profile}
        
    prefs_file = bg_dir / "preferences.json"
    existing_data = {}
    if prefs_file.exists():
        try:
            with open(prefs_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = {}
            
    candidate_data = {
        "name": profile.get("name", "Candidate"),
        "school": profile.get("school", "University"),
        "degree": profile.get("degree", "B.S. in Computer Science / Data Science"),
        "graduation": profile.get("graduation", "May 2027"),
        "location": profile.get("location", "City, Country"),
        "work_authorization": profile.get("work_authorization", "Needs Sponsorship / International"),
        "email": profile.get("email", "candidate@example.com"),
        "phone": profile.get("phone", "+1 555 0100"),
        "linkedin": profile.get("linkedin", "https://linkedin.com/in/username"),
        "github": profile.get("github", "https://github.com/username")
    }
    
    target_domains = profile.get("target_domains", ["Software Engineering", "Machine Learning", "Data Systems"])
    comp_floor = float(profile.get("minimum_hourly_usd", 20.0))
    
    prefs_payload = {
        "candidate": candidate_data,
        "modality": existing_data.get("modality", {
            "ranking": ["remote", "hybrid", "onsite"],
            "remote_preference": "highest"
        }),
        "schedule": existing_data.get("schedule", {
            "weekly_availability_grid": build_default_schedule(),
            "target_weekly_hours": 20,
            "max_weekly_hours": 30
        }),
        "compensation": {
            "minimum_hourly_usd": comp_floor,
            "currency": "USD"
        },
        "career_goals": {
            "target_domains": target_domains,
            "disallowed_industries": ["Crypto", "Gambling"]
        }
    }
    
    with open(prefs_file, "w", encoding="utf-8") as f:
        json.dump(prefs_payload, f, indent=2, ensure_ascii=False)
        
    # Generate starter resume if template exists
    template_tex = cv_dir / "template.tex"
    clean_name = candidate_data["name"].replace(" ", "_")
    output_tex = cv_dir / f"{clean_name}_Resume.tex"
    if template_tex.exists() and generate_resume_tex:
        generate_resume_tex.generate_resume(template_tex, output_tex, candidate_data)
        
    return {
        "success": True,
        "dry_run": False,
        "preferences_json": str(prefs_file),
        "resume_tex": str(output_tex) if output_tex.exists() else None
    }

def interactive_wizard() -> Dict[str, Any]:
    print("\n========================================================")
    print("  CAREER VAULT SETUP WIZARD (Data Science & SWE)        ")
    print("========================================================\n")
    name = input("Candidate Full Name: ").strip() or "Candidate"
    school = input("University / Institution: ").strip() or "University"
    degree = input("Degree / Major (e.g. B.S. in Data Science): ").strip() or "B.S. in Data Science"
    graduation = input("Expected Graduation (e.g. May 2027): ").strip() or "May 2027"
    location = input("Current Location (City, Country): ").strip() or "Querétaro, Mexico"
    visa = input("Work Authorization / Visa Status: ").strip() or "Needs Sponsorship"
    email = input("Contact Email: ").strip() or "candidate@example.com"
    phone = input("Contact Phone: ").strip() or "+1 555 0100"
    linkedin = input("LinkedIn URL: ").strip() or "https://linkedin.com"
    github = input("GitHub URL: ").strip() or "https://github.com"
    
    return {
        "name": name,
        "school": school,
        "degree": degree,
        "graduation": graduation,
        "location": location,
        "work_authorization": visa,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "target_domains": ["Software Engineering", "Machine Learning", "Data Platforms"]
    }

def main():
    parser = argparse.ArgumentParser(description="Career Vault Onboarding Wizard")
    parser.add_argument("--interactive", action="store_true", help="Run interactive prompt wizard")
    parser.add_argument("--json", help="Path to profile JSON input file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate configuration without writing files")
    args = parser.parse_args()
    
    vault_root = Path(__file__).resolve().parent
    
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            profile = json.load(f)
    elif args.interactive or not len(sys.argv) > 1:
        profile = interactive_wizard()
    else:
        print("[INFO] Use --interactive or --json to configure vault. Exiting.")
        sys.exit(0)
        
    result = configure_vault(vault_root, profile, dry_run=args.dry_run)
    print("\n[SUCCESS] Vault configured successfully:")
    print(f"  - Preferences: {result.get('preferences_json')}")
    if result.get('resume_tex'):
        print(f"  - Starter LaTeX Resume: {result.get('resume_tex')}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
py -3.11 -m pytest tests/test_setup_vault.py
```
Expected: PASS (2 passed).

- [ ] **Step 5: Commit setup wizard**

```bash
git add setup_vault.py tests/test_setup_vault.py
git commit -m "feat(vault): add interactive setup wizard for DS and SWE onboarding"
```

---

### Task 5: Starter Templates & Background Markdown Blueprints

**Files:**
- Create: `001-background/templates/experience-blueprint.md`
- Create: `001-background/templates/project-blueprint.md`

- [ ] **Step 1: Create `001-background/templates/experience-blueprint.md`**

Create `001-background/templates/experience-blueprint.md`:
```markdown
---
created: YYYY-MM-DD
type: experience
tags: [experience, background, swe, data-science]
status: active
---

### Organization / Company — Role Title
*Modality (Remote/Hybrid/Onsite) | Location | Month YYYY – Month YYYY*
*Official Repo / Project URL:* [link](https://...)

- **Context & Problem:** Institutional scale, traffic volume, or operational bottleneck being addressed.
- **Stack & Architecture:** Languages (Python, C++, SQL), frameworks (PyTorch, FastAPI, Spark), and hardware/cloud platforms.
- **Impact & Metrics (Google XYZ):** Accomplished [X], measured by [Y] (e.g. latency, throughput, accuracy, cost), by doing [Z].
- **Testing & Verification:** Test coverage, benchmarks, automated validation, and peer review.
```

- [ ] **Step 2: Create `001-background/templates/project-blueprint.md`**

Create `001-background/templates/project-blueprint.md`:
```markdown
---
created: YYYY-MM-DD
type: project
tags: [project, portfolio, swe, ai]
status: active
---

### Project Title
*Technologies: Language, Framework, Database, Tooling | Month YYYY – Month YYYY*
*Repository:* [github.com/username/project](https://github.com/...)

- **Overview:** Concise problem statement and architectural objective.
- **Key Technical Highlights:**
  - Designed and implemented [system component], achieving [quantifiable metric] under [conditions].
  - Optimized [bottleneck], reducing compute footprint or latency by [X\%].
- **Verification & Reproducibility:** Test suite specs, benchmark scripts, and deployment instructions.
```

- [ ] **Step 3: Commit blueprints**

```bash
git add 001-background/templates/
git commit -m "docs(background): add DS and SWE experience and project blueprints"
```

---

### Task 6: Public-Ready Root `README.md`

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

Create `README.md` featuring:
- Hero header: Career Vault — Autonomous AI-Powered Career Operating System for Data Scientists & Software Engineers.
- Core architecture (`001-background` through `004-work-opportunities`).
- Setup & Quickstart instructions (`python setup_vault.py`).
- 11 active skills showcase table.
- Build tooling (`compile_cv.py`, `validate_ats.py`).

- [ ] **Step 2: Commit `README.md`**

```bash
git add README.md
git commit -m "docs: add comprehensive root README for open-source Career Vault"
```

---

### Task 7: Full Integration Verification

**Files:**
- Run full test suite across `tests/`

- [ ] **Step 1: Execute all unit tests**

Run:
```powershell
py -3.11 -m pytest tests/ -v
```
Expected: All tests pass (43 + 6 new tests = 49+ tests passing).

- [ ] **Step 2: Dry-run setup wizard smoke test**

Run:
```powershell
py -3.11 setup_vault.py --dry-run
```
Expected: Success code 0.

- [ ] **Step 3: Final Git status check**

Run:
```powershell
git status
```
Expected: Clean working tree.

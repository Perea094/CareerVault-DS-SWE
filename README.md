# Career Vault — Autonomous AI-Powered Career Operating System for Data Scientists & Software Engineers

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Obsidian Vault](https://img.shields.io/badge/Obsidian-Vault-purple.svg)](https://obsidian.md/)
[![ATS Validated](https://img.shields.io/badge/ATS-100%25%20Parseable-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/pytest-passing-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source, agentic personal career operating system built on top of **Obsidian**, **Python**, **LaTeX**, and **Autonomous Agent Skills**. Designed for Data Science and Software Engineering candidates to autonomously scout opportunities, evaluate eligibility against live constraints, tailor ATS-optimized resumes with 100% factual integrity, manage application pipelines, and draft hyper-targeted outreach and interview dossiers.

---

## 🏛️ System Architecture

The vault is structured into four functional layers designed for separation of concerns, zero hallucinations, and temporal traceability:

```
CareerVault-DS-SWE/
├── 001-background/               # Ground Truth Layer
│   ├── candidate_profile.py      # Dynamic profile loader
│   ├── preferences.json / .md    # Living career constraints & availability
│   ├── templates/                # DS & SWE experience & project blueprints
│   ├── education/                # Verified coursework, transcripts & syllabi
│   ├── experiences/              # Verified internships, work history & metrics
│   └── projects/                 # Verified software, ML systems & benchmarks
│
├── 002-cv/                       # Tailoring & LaTeX Compilation Layer
│   ├── template.tex              # Modular ATS-compliant LaTeX base template
│   ├── Custom/                   # Tailored 1-to-1 resume drafts
│   └── scripts/                  # compile_cv.py, validate_ats.py, generate_resume_tex.py
│
├── 003-extra/                    # Prompts & Agent Systems Layer
│   ├── prompts/                  # System prompts, review rubrics & STAR templates
│   └── scripts/                  # Auxiliary agent tooling
│
├── 004-work-opportunities/       # Scout & Pipeline Management Layer
│   ├── database/                 # opportunities.json, archived_opportunities.json
│   ├── pipeline/                 # application-pipeline.md (Obsidian Kanban)
│   ├── scripts/                  # scan_opportunities.py, update_pipeline.py
│   └── <company>/                # Saved job postings and triage evaluation notes
│
└── .agents/skills/               # 11 Autonomous Agent Skills & CLI Tooling
```

### 1. `001-background/` — Ground Truth Layer
The single source of truth for the entire operating system. All resume points, cover letters, and interview prep dossiers **must strictly ground** in files located here.
- **Dynamic Candidate Profile**: Extracted from `preferences.json` by `candidate_profile.py`.
- **Career Preferences & Constraints**: Hard rules for work authorization/visa requirements, hourly pay floors, disallowed industries, and weekly availability grids.
- **Blueprints**: Standardized Markdown templates enforcing Google XYZ (`Accomplished [X], measured by [Y], by doing [Z]`) and STAR frameworks.

### 2. `002-cv/` — Tailoring & LaTeX Compilation Layer
The document generation engine. Follows the principle: **Markdown-first for drafting, LaTeX strictly as the final compilation move.**
- **Modular LaTeX Templates**: Single-page, mathematically formatted layouts without multi-column parsing traps.
- **Automated Compiler (`compile_cv.py`)**: Auto-detects Tectonic, pdfLaTeX, XeLaTeX, or latexmk and generates a high-resolution PNG preview for Obsidian.
- **ATS Validator (`validate_ats.py`)**: Uses `pdfplumber` to verify page count budget, core section detection, contact link parseability, and text density.

### 3. `003-extra/` — Prompts & Agent Systems Layer
Houses recruiter system prompts, evaluation rubrics, behavioral STAR coaching guidelines, and auxiliary automation scripts.

### 4. `004-work-opportunities/` — Scout & Pipeline Management Layer
Tracks prospective, active, and completed job applications.
- **Scout Engine (`scan_opportunities.py`)**: Daily automated ingest across 19 GitHub repositories and community feeds.
- **Eligibility Filter**: Matches requirements against candidate location, visa sponsorship requirements, and graduation timeline.
- **Kanban Board**: Real-time visual lifecycle tracking across 8 stages (`wishlist`, `applied`, `oa_received`, `screening`, `interview`, `offer`, `rejected`, `withdrawn`).

---

## 🚀 Quickstart Guide

Follow these steps to set up your personal Career Vault:

### 1. Clone the Repository
```bash
git clone https://github.com/Perea094/CareerVault-DS-SWE.git
cd CareerVault-DS-SWE
```

### 2. Run the Interactive Setup Wizard
Initialize your personal profile, set your university background, degree, target domains, and generate a customized starter LaTeX resume:
```bash
python setup_vault.py --interactive
```
*Non-interactive option with profile JSON:*
```bash
python setup_vault.py --json profile.json
```

### 3. Launch the Preference Manager Web UI
Adjust your weekly availability grid, set minimum hourly compensation, rank remote vs. hybrid preferences, and run live opportunity audits:
```bash
python .agents/skills/preference-manager/scripts/preference_server.py --open
```

### 4. Run the Opportunity Scout
Scan 19 upstream internship and new grad repositories, deduplicate listings, and filter by work authorization and candidate constraints:
```bash
python 004-work-opportunities/scripts/scan_opportunities.py
```

### 5. Compile Your Resume
Build an ATS-optimized, publication-ready PDF from LaTeX and generate an Obsidian image preview:
```bash
python 002-cv/scripts/compile_cv.py 002-cv/template.tex
```

### 6. Audit ATS Parseability
Inspect the compiled PDF with `pdfplumber` to ensure 100% ATS machine readability, single-page compliance, and contact link extraction:
```bash
python 002-cv/scripts/validate_ats.py 002-cv/template.pdf
```

---

## ⚡ 11 Autonomous Agent Skills

The Career Vault includes 11 specialized agent skills under `.agents/skills/`:

| Skill | Path | Description & Workflow |
| :--- | :--- | :--- |
| **`add-experience-curriculum`** | `.agents/skills/add-experience-curriculum/` | Ingests new jobs, university challenges, or GitHub repositories into `001-background/` enforcing Google XYZ metrics and verification scripts. |
| **`application-tracker`** | `.agents/skills/application-tracker/` | Manages 8-stage application lifecycle transitions and syncs Obsidian Kanban pipeline boards (`application-pipeline.md`). |
| **`cover-letter-writer`** | `.agents/skills/cover-letter-writer/` | Crafts tailored, 3-paragraph cover letters grounded 100% in verified background assets matching target role requirements. |
| **`expert-recruiter`** | `.agents/skills/expert-recruiter/` | Audits resumes against job descriptions, calculates ATS keyword overlap, identifies gaps, and scores recruiter pass rates. |
| **`interview-prep`** | `.agents/skills/interview-prep/` | Generates comprehensive interview dossiers with role-matched STAR stories, technical cheat sheets, and reverse interviewer questions. |
| **`markitdown`** | `.agents/skills/markitdown/` | Ingests and converts external documents (PDF, DOCX, PPTX, XLSX, HTML, audio) into clean Obsidian Markdown. |
| **`networking-outreach`** | `.agents/skills/networking-outreach/` | Creates targeted 3-tier cold outreach, alumni connections, and hiring manager referral requests. |
| **`obsidian-cli`** | `.agents/skills/obsidian-cli/` | Command-line integration to query tags, update frontmatter properties, inspect backlinks, and manage vault tasks. |
| **`opportunity-scout`** | `.agents/skills/opportunity-scout/` | Scrapes 19 tech internship and new grad GitHub feeds, scores eligibility, and updates the local opportunity database. |
| **`preference-manager`** | `.agents/skills/preference-manager/` | Runs local web server (`:8080`) and REST API to manage availability matrices, modality rankings, and audit matching rules. |
| **`tailored-cv`** | `.agents/skills/tailored-cv/` | Generates customized 1-to-1 resume drafts or role archetypes in Markdown, linking verified achievements to specific job postings. |

---

## 🧪 Verification & Test Suite

The repository is covered by an automated test suite verifying candidate profile extraction, LaTeX resume generation, ATS validation, opportunity scanning, pipeline updates, and agent skills.

To execute the full test suite:

```bash
pytest tests/ -v
```

*(On Windows systems using the Python launcher: `py -3.11 -m pytest tests/ -v`)*

### Core Test Modules:
- `tests/test_candidate_profile.py`: Verifies dynamic profile fallback and JSON schema parsing.
- `tests/test_generate_resume_tex.py`: Validates LaTeX special-character escaping and placeholder substitution.
- `tests/test_setup_vault.py`: Tests the setup wizard, dry-run mode, and automated template generation.
- `tests/test_compile_cv.py`: Tests LaTeX compiler detection and CLI argument generation.
- `tests/test_validate_ats.py`: Verifies PDF parsing, header detection, and ATS penalty scoring.
- `tests/test_application_tracker.py`: Tests pipeline stage transitions and Kanban synchronization.
- `tests/test_networking_outreach.py`: Tests 3-tier message generation and profile grounding.
- `tests/test_interview_prep.py`: Tests interview dossier generation and STAR mapping.
- `tests/test_preference_server.py`: Tests REST API endpoints, CORS handling, and Markdown syncing.
- `tests/test_opportunity_scout.py`: Tests scraper deduplication, parser adapters, and tier ranking.

---

## 📜 Core Operating Principles

1. **Factual Integrity (Zero Hallucination)**: No skill or prompt may fabricate metrics, technologies, or experience points. Everything must trace directly to `001-background/`.
2. **Markdown-First, LaTeX Final**: All drafting, comparison, review, and editing occurs in human-readable Markdown. LaTeX is strictly the final typesetting step.
3. **Temporal Traceability**: All notes maintain creation dates, update timestamps, and status tags (`summer-2027`, `active`, etc.) in flat YAML frontmatter for seamless Obsidian integration.
4. **Local & Private**: All data, preferences, notes, and pipelines live locally in your vault without dependency on external third-party career tracking SaaS platforms.

---

## 📄 License

Distributed under the [MIT License](LICENSE).

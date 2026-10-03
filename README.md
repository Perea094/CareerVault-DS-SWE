# Career Vault — Autonomous AI-Powered Career Operating System for Data Scientists & Software Engineers

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Obsidian Vault](https://img.shields.io/badge/Obsidian-Vault-purple.svg)](https://obsidian.md/)
[![ATS Validated](https://img.shields.io/badge/ATS-100%25%20Parseable-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/pytest-75%20passing-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source, agentic personal career operating system built on top of **Obsidian**, **LaTeX**, **Python**, and **Autonomous Agent Skills**. Designed for Data Science and Software Engineering candidates to autonomously scout opportunities, evaluate eligibility against live constraints, tailor ATS-optimized resumes with 100% factual integrity, manage application pipelines, and draft hyper-targeted outreach and interview dossiers.

---

> [!IMPORTANT]
> ### 🤖 Agent-First Operating Model
> **This project is specifically intended to be used with the help of an Agentic AI Harness** (such as **Google Antigravity**, **Claude Code**, **Cursor Agent**, **OpenCode**, or similar terminal/IDE agents).
>
> While all underlying Python scripts, parsers, and LaTeX compilers are fully functional standalone tools, **they are designed primarily for the AI agent to execute autonomously on your behalf**. Rather than manually running CLI commands for each task, your primary workflow is simply to collaborate with your AI agent in natural language. The agent automatically discovers the vault rules (`GEMINI.md` / `AGENTS.md`) and leverages the 11 specialized agent skills in `.agents/skills/`.

---

## 🚀 Quickstart Guide

Get your personal Career Vault up and running in minutes:

### 1. Clone the Repository
```bash
git clone https://github.com/Perea094/CareerVault-DS-SWE.git
cd CareerVault-DS-SWE
```

### 2. Run the Starter Setup Wizard & Auto-Install Dependencies
Initialize your candidate profile, set your degree and target domains, auto-create a virtual environment (`.venv`), and install dependencies with a single command:
- **Windows (1-Click)**: Double-click `setup.bat` or run:
  ```cmd
  setup.bat
  ```
- **macOS / Linux (1-Command)**:
  ```bash
  chmod +x setup.sh && ./setup.sh
  ```
- **Direct Python**:
  ```bash
  python setup_vault.py --interactive --install-deps
  ```
*(Or non-interactively with a pre-filled JSON profile: `python setup_vault.py --json profile.json`)*

> [!TIP]
> **Zero-Dependency Markdown Core & Optional Obsidian CLI**:
> Career Vault operates 100% on standard flat Markdown (`.md`) and JSON (`.json`) files. You do **not** need Obsidian or the Obsidian CLI installed to use this operating system—any AI agent can read, search, and edit files natively using standard tools. The Obsidian desktop app and Obsidian CLI are optional accelerators.

### 3. Open in Your Agentic AI Harness
Open the `CareerVault-DS-SWE` folder inside your preferred agentic environment.

The agent will automatically load the workspace instructions and register the 11 autonomous skills under `.agents/skills/`.

### 4. Instruct Your Agent Using Skills
Simply chat with your agent. Instruct it to perform career tasks, and it will execute the appropriate skills and internal scripts behind the scenes:

| Desired Action | Example Agent Prompt | Activated Skill(s) | Internal Agent Actions |
| :--- | :--- | :--- | :--- |
| **Scout Opportunities** | *"Scout recent data science and ML internships and evaluate them against my preferences."* | `opportunity-scout`<br>`preference-manager` | Runs `scan_opportunities.py`, scores listings by domestic/remote viability, updates `opportunities.json`. |
| **Tailor Resume** | *"Tailor my CV for this Machine Learning Engineer posting [link/text] and generate an ATS-checked PDF."* | `tailored-cv`<br>`expert-recruiter` | Selects relevant projects from `001-background/`, drafts 1-page CV in `002-cv/Custom/`, compiles LaTeX, and validates ATS score. |
| **Document Experience** | *"Ingest my latest distributed systems challenge from github.com/user/repo into my verified background."* | `add-experience-curriculum` | Analyzes code/metrics, enforces Google XYZ format, and creates an audit-ready note in `001-background/projects/`. |
| **Track Applications** | *"I just got an interview request for Stripe. Update my pipeline and prepare an interview dossier."* | `application-tracker`<br>`interview-prep` | Transitions role to `interview` on Kanban board, extracts role-matched STAR stories into an interview prep guide. |
| **Cold Outreach** | *"Draft 3-tier networking messages for alumni, recruiters, and engineering managers at Databricks."* | `networking-outreach` | Formulates targeted LinkedIn/email templates grounded in your verified achievements. |
| **Adjust Preferences** | *"Launch the preference portal so I can update my weekly availability calendar."* | `preference-manager` | Boots local web UI (`preference_server.py --open`) and synchronizes flat YAML frontmatter in Obsidian. |

---

## ⚡ 11 Autonomous Agent Skills

The Career Vault equips AI agents with 11 specialized skills located in `.agents/skills/`:

| Skill | Directory | Primary Role & Capabilities |
| :--- | :--- | :--- |
| **`add-experience-curriculum`** | `.agents/skills/add-experience-curriculum/` | Ingests new jobs, challenges, or GitHub repositories into `001-background/` enforcing Google XYZ metrics (`Accomplished [X], measured by [Y], by doing [Z]`). |
| **`application-tracker`** | `.agents/skills/application-tracker/` | Manages 8-stage application lifecycle transitions and syncs Obsidian Kanban pipeline boards (`application-pipeline.md`). |
| **`cover-letter-writer`** | `.agents/skills/cover-letter-writer/` | Crafts tailored, 3-paragraph cover letters grounded 100% in verified background assets matching target role requirements. |
| **`expert-recruiter`** | `.agents/skills/expert-recruiter/` | Audits resumes against job descriptions, calculates ATS keyword overlap, identifies gaps, and scores recruiter pass rates. |
| **`interview-prep`** | `.agents/skills/interview-prep/` | Generates comprehensive interview dossiers with role-matched STAR stories, technical cheat sheets, and reverse interviewer questions. |
| **`markitdown`** | `.agents/skills/markitdown/` | Ingests and converts external documents (PDF, DOCX, PPTX, XLSX, HTML, audio) into clean Obsidian Markdown. |
| **`networking-outreach`** | `.agents/skills/networking-outreach/` | Creates targeted 3-tier cold outreach, alumni connections, and hiring manager referral requests. |
| **`obsidian-cli`** | `.agents/skills/obsidian-cli/` | Command-line integration to query tags, update frontmatter properties, inspect backlinks, and manage vault tasks. |
| **`opportunity-scout`** | `.agents/skills/opportunity-scout/` | Scrapes 19 tech internship and new grad GitHub feeds, scores eligibility dynamically worldwide, and updates the local opportunity database. |
| **`preference-manager`** | `.agents/skills/preference-manager/` | Runs local web server and REST API to manage 7-day availability matrices, modality rankings, and audit matching rules. |
| **`tailored-cv`** | `.agents/skills/tailored-cv/` | Generates customized 1-to-1 resume drafts or role archetypes in Markdown, linking verified achievements to specific job postings. |

---

## 🏛️ System Architecture

The vault is structured into four functional layers designed for separation of concerns, zero hallucinations, and temporal traceability:

```
CareerVault-DS-SWE/
├── 001-background/               # Ground Truth Layer
│   ├── candidate_profile.py      # Dynamic profile loader
│   ├── preferences.json / .md    # Living career constraints & availability
│   ├── templates/                # DS & SWE blueprints (experience, project, education)
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
│   ├── scripts/                  # scan_opportunities.py, prune_opportunities.py
│   └── <company>/                # Saved job postings and triage evaluation notes
│
└── .agents/skills/               # 11 Autonomous Agent Skills & CLI Tooling
```

### 1. `001-background/` — Ground Truth Layer
The single source of truth for the entire operating system. All resume points, cover letters, and interview prep dossiers **must strictly ground** in files located here.
- **Dynamic Candidate Profile**: Extracted from `preferences.json` by `candidate_profile.py`.
- **Career Preferences & Constraints**: Living rules for work authorization/visa requirements, hourly pay floors, disallowed industries, and weekly availability grids.
- **Blueprints**: Standardized Markdown templates enforcing Google XYZ (`Accomplished [X], measured by [Y], by doing [Z]`) and STAR frameworks.

### 2. `002-cv/` — Tailoring & LaTeX Compilation Layer
The document generation engine. Follows the principle: **Markdown-first for drafting, LaTeX strictly as the final compilation move.**
- **Modular LaTeX Templates**: Single-page, mathematically formatted layouts without multi-column parsing traps.
- **Automated Compiler (`compile_cv.py`)**: Auto-detects Tectonic, pdfLaTeX, XeLaTeX, or latexmk and generates a high-resolution PNG preview for Obsidian.
- **Universal ATS Validator (`validate_ats.py`)**: Evaluates `.pdf`, `.md`, `.tex`, and `.txt` files to verify single-page budget, core section detection, contact link parseability, and text density.

### 3. `003-extra/` — Prompts & Agent Systems Layer
Houses recruiter system prompts, evaluation rubrics, behavioral STAR coaching guidelines, and auxiliary automation scripts. Can be consumed by any AI agent framework (Antigravity, Claude, OpenAI, Cursor).

### 4. `004-work-opportunities/` — Scout & Pipeline Management Layer
Tracks prospective, active, and completed job applications.
- **Scout Engine (`scan_opportunities.py`)**: Daily automated ingest across 19 GitHub repositories and community feeds.
- **Worldwide Dynamic Viability**: Matches requirements against candidate's home location, visa sponsorship requirements, and graduation timeline across any country globally.
- **Kanban Board**: Real-time visual lifecycle tracking across 8 stages (`wishlist`, `applied`, `oa_received`, `screening`, `interview`, `offer`, `rejected`, `withdrawn`).

---

## 🧪 Verification & Test Suite

The repository is covered by an automated test suite verifying candidate profile extraction, LaTeX resume generation, ATS validation, opportunity scanning, pipeline updates, and agent skills.

To execute the test suite:

```bash
pytest tests/ -v
```

*(On Windows systems using the Python launcher: `py -3.11 -m pytest tests/ -v`)*

**75 unit & integration tests pass 100%**, covering:
- Dynamic worldwide opportunity scanning and tiering (`test_scan_opportunities.py`)
- Candidate profile resolution and multi-tier fallbacks (`test_candidate_profile.py`)
- LaTeX escaping and template rendering (`test_generate_resume_tex.py`)
- ATS score calculation across PDF, LaTeX, and Markdown (`test_validate_ats.py`)
- Preference server REST API and Obsidian Markdown sync (`test_preference_server.py`, `test_preference_models.py`, `test_audit_preferences.py`)
- Application lifecycle transitions and Kanban boards (`test_application_tracker.py`)
- 3-tier networking outreach generation (`test_networking_outreach.py`)
- Interview dossier compilation and STAR stories (`test_interview_prep.py`)
- Interactive setup wizard and dry-run execution (`test_setup_vault.py`)

---

## 📜 Core Operating Principles

1. **Agent-First Design**: Designed for natural-language pair programming with an agentic AI harness rather than manual maintenance.
2. **Factual Integrity (Zero Hallucination)**: No skill or prompt may fabricate metrics, technologies, or experience points. Everything must trace directly to `001-background/`.
3. **Markdown-First, LaTeX Final**: All drafting, comparison, review, and editing occurs in human-readable Markdown. LaTeX is strictly the final typesetting step.
4. **Temporal Traceability**: All notes maintain creation dates, update timestamps, and status tags (`summer-2027`, `active`, etc.) in flat YAML frontmatter for seamless Obsidian integration.
5. **Local, Private & Global**: All data, preferences, notes, and pipelines live locally in your vault without SaaS lock-in, and adapt dynamically to candidates anywhere in the world.

---

## 📄 License

Distributed under the [MIT License](LICENSE).

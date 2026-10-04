# Career Vault — Data Science & Software Engineering Career Operating System

## 1. Context & Purpose
- **Workspace**: Active Obsidian vault (`CareerVault-DS-SWE`).
- **Objective**: Central hub for personal background documentation, verified experiences/projects, job opportunity tracking, and tailored CV generation for Data Science and Software Engineering candidates.
- **Candidate Profile**: Configured dynamically via `setup_vault.py` or the Preference Manager UI. All active personal constraints, career goals, and evaluation criteria live dynamically in `001-background/preferences.md` and `001-background/preferences.json`.

---

## 2. Core Principles
- **Markdown-First**: All notes, research, opportunity evaluations, and working CV drafts must be written in Markdown (`.md`).
- **LaTeX as Final Move**: LaTeX (`.tex`) in `002-cv/` is strictly the final compilation step when generating an application-ready PDF.
- **Temporality Tracking & YAML Metadata**: Every file must maintain temporal traceability—either in its filename (e.g., `YYYY-MM-DD`) or inside its YAML frontmatter. Leverage YAML frontmatter in Markdown notes (`created`, `updated`, `type`, `tags`, `status`, etc.) to facilitate sorting, filtering, and Obsidian property management.
  - *Obsidian Property Compatibility*: Obsidian only supports flat properties. Never create nested YAML mappings/dictionaries.
  - *Obsidian Tag Rules*: All tags must contain non-numerical characters (e.g., use `summer-2027`, never pure numbers like `2027` which causes YAML type-mismatch warnings `⚠️` in Obsidian).
- **Dynamic Source of Truth**: Never duplicate or hardcode evaluation rules. Always consult `001-background/preferences.md` directly for current constraints and preferences.
- **Factual Integrity**: Never invent experiences, metrics, or technical skills. All resume points must be grounded in verified background files under `001-background/`.

---

## 3. Directory Overview
- `001-background/`: Ground truth repository (experiences, technical projects, historical CVs, and `preferences.md`).
- `002-cv/`: Master CV templates, validation scripts, and job-tailored drafts (`Custom/`).
- `003-extra/`: Prompt templates, system instructions, and auxiliary tools.
- `004-work-opportunities/`: Tracked job postings, opportunity database, and Kanban pipeline.

---

## 4. Flexible Workflows

### Workflow 0: Onboarding & Kickoff ("Hi, I already ran the setup script, what is the next step?")
When the candidate initiates the session with this kickoff prompt:
1. Inspect `001-background/preferences.json` and `001-background/preferences.md` to confirm configured candidate identity, targets, and availability.
2. Audit `001-background/` for verified records (`001-background/experiences/`, `001-background/projects/`, `001-background/education/`).
3. Verify starter LaTeX resume in `002-cv/` and run `002-cv/scripts/validate_ats.py`.
4. Evaluate Template Status & Enforce Background Ingestion:
   - If the starter resume contains abstract structural placeholders (`[Company...]`, `[Project...]`) and `001-background/` has no verified records:
     - **NEVER** claim the resume is ready, application-grade, or passed 100/100.
     - Transparently inform the candidate that their contact profile is configured, but their CV is currently an **abstract structural template with placeholders** with **0 verified records** in `001-background/`.
     - **Mandatory Primary Move (High-Priority Prompt)**: Steer the candidate to **Path A: Ingest Verified Background** (using `add-experience-curriculum`, uploading a past CV into `001-background/previous_cv/`, or documenting recent projects/roles) before tailoring or applying.
   - If verified records already exist in `001-background/`:
     - Compile their true baseline CV and present Path B (Scout Global Tech Opportunities) and Path C (Tailor for a Target Role).

### Workflow 1: Opportunity Intake & Triage
1. Save the job description in Markdown under `004-work-opportunities/` with YAML frontmatter tracking temporality and metadata (e.g., `date`, `company`, `role`, `status`, `tags`).
2. Review the role against the active criteria in `001-background/preferences.md`.
3. File the opportunity into the appropriate folder (e.g., eligible vs. non-eligible) and append a concise evaluation note highlighting relevant matches and gaps.

### Workflow 2: Tailoring CVs (Powered by `tailored-cv`)
1. Identify relevant skills, projects, and experiences in `001-background/` that match the target role.
2. For single opportunities, draft a dedicated 1-to-1 CV in Markdown under `002-cv/Custom/`. For multiple opportunities, evaluate stack overlap to either generate 1-to-1 CVs or cluster them into role archetypes.
3. Review and iterate on the Markdown draft.
4. **Final Step**: When approved, format into LaTeX using `002-cv/template.tex` for final PDF compilation.

### Workflow 3: Background Maintenance
- When new projects, coursework, or achievements occur, document them in `001-background/` first so they are immediately available for future CV tailoring.

---

## 5. Obsidian CLI Guidelines & Universality
- **Optional Accelerator**: The official `obsidian` CLI command (`Obsidian.com`) is an optional tool for vaults open in the Obsidian desktop application. When available, use it for convenient indexed actions:
  - **Search**: `obsidian search query="..."` or `obsidian search:context query="..."`
  - **Metadata**: `obsidian property:read` / `obsidian property:set`
  - **Tasks**: `obsidian tasks todo verbose` / `obsidian task done ref="..."`
  - **Tags**: `obsidian tags counts`
- **Native File-System Fallback**: If `obsidian` is not installed or not in `PATH`, agents operate 100% autonomously using standard file tools (`view_file`, `write_to_file`, `replace_file_content`, and grep). All vault skills and formats are completely Markdown-native and independent of Obsidian.

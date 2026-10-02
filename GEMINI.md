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

## 5. Obsidian CLI Guidelines
The official `obsidian` CLI command is available in the terminal (`Obsidian.com`). Use it when helpful for vault-level actions:
- **Search**: `obsidian search query="..."` or `obsidian search:context query="..."`
- **Metadata**: `obsidian property:read` / `obsidian property:set`
- **Tasks**: `obsidian tasks todo verbose` / `obsidian task done ref="..."`
- **Tags**: `obsidian tags counts`

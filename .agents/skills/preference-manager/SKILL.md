---
name: preference-manager
description: Manage, edit, and audit Diego Perea León's career preferences, weekly availability grid, work modality rankings, compensation floors, and opportunity alignment scoring via an interactive survey web UI or CLI.
---

# preference-manager

Interactive survey web UI, dual-file persistence engine, and AI opportunity alignment auditor for managing **Diego Perea León's** career preferences and active job-search constraints.

Maintains strict synchronization between the rich JSON schema ([`001-background/preferences.json`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.json)) and Obsidian-compliant flat frontmatter Markdown ([`001-background/preferences.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.md)), while scoring tracked opportunities against live constraints.

---

## When to Use & Triggering

Summon or trigger this skill whenever:
- Diego needs to update his weekly schedule, available hours, or semester course block commitments.
- Modality preferences change (e.g. Remote vs. Hybrid vs. Onsite priority order).
- Financial compensation floors (minimum hourly rate in USD) or benefits priorities are revised.
- Target domains (GenAI, RL, Vision, NLP, Systems) or dealbreakers (e.g. Crypto, unpaid overtime) are adjusted.
- An opportunity audit is required to filter and rank postings in [`004-work-opportunities/`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/004-work-opportunities/) against Diego's active constraints.

**Do NOT use for**:
- Ingesting raw experiences or academic projects (use [`add-experience-curriculum`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/add-experience-curriculum/SKILL.md)).
- Scraping external job feeds (use [`opportunity-scout`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/opportunity-scout/SKILL.md)).
- Tailoring individual resumes/CVs (use [`tailored-cv`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/tailored-cv/SKILL.md)).

---

## Target Vault Paths & Key Components

- **Web Server & REST API:** [`.agents/skills/preference-manager/scripts/preference_server.py`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/scripts/preference_server.py)
- **Data Model & Sync Engine:** [`.agents/skills/preference-manager/scripts/preference_models.py`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/scripts/preference_models.py)
- **AI Opportunity Audit Script:** [`.agents/skills/preference-manager/scripts/audit_preferences.py`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/scripts/audit_preferences.py)
- **Web App Assets:**
  - HTML structure: [`.agents/skills/preference-manager/web/index.html`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/web/index.html)
  - Styling (glassmorphism/responsive): [`.agents/skills/preference-manager/web/style.css`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/web/style.css)
  - Interactive UI logic: [`.agents/skills/preference-manager/web/app.js`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/web/app.js)
- **Master Preference Ground Truth (JSON):** [`001-background/preferences.json`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.json)
- **Obsidian Human-Readable Notes (MD):** [`001-background/preferences.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.md)
- **Audited Opportunities Database:** [`004-work-opportunities/database/opportunities.json`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/004-work-opportunities/database/opportunities.json)
- **Generated Audit Report:** [`004-work-opportunities/opportunities-preference-audit.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/004-work-opportunities/opportunities-preference-audit.md)

---

## End-to-End Workflow Guide

### Step 1: Launch the Interactive Web Survey

Start the dedicated local preference server from PowerShell:

```powershell
.\.venv\Scripts\python.exe .agents/skills/preference-manager/scripts/preference_server.py --open
```

*(Alternatively, use `python .agents/skills/preference-manager/scripts/preference_server.py --open` if your active shell has the virtual environment activated).*

- **Default Port:** `8765` (customizable via `--port <PORT>`).
- **Browser:** The `--open` flag automatically opens the default web browser to `http://127.0.0.1:8765/`.
- If the browser does not open automatically, navigate to `http://127.0.0.1:8765/` manually.

### Step 2: Configure Career Preferences in the Web UI

The web UI guides Diego through structured configuration cards:

1. **Work Modality Ranking:**
   - Drag-and-drop or use up/down reorder buttons to rank `Remote`, `Hybrid`, and `Onsite`.
2. **Weekly Availability & Schedule Grid:**
   - 7 days (Monday–Sunday) across 7 two-hour blocks (08:00–10:00, 10:00–12:00, 12:00–14:00, 14:00–16:00, 16:00–18:00, 18:00–20:00, 20:00–22:00).
   - Click or drag-select cells to cycle through 3 slot states:
     - `available` (open for work/projects, adds 2 hrs to weekly tally)
     - `classes` (academic coursework / Tec commitments)
     - `busy` (personal blocks, study, or other commitments)
   - Real-time weekly available hours calculator (summing active `available` slots).
3. **Weekly Hours & Flexibility:**
   - Target range (e.g., `20-30` hours/week during semester, `40` max manageable).
   - Timezone overlap preferences and async/sync communication balance.
4. **Location & Visa Status:**
   - Base location (`Querétaro, Mexico`).
   - US work authorization (None / Needs J-1/F-1 CPT/OPT sponsorship or international contractor agreement).
5. **Compensation & Benefits:**
   - Minimum hourly rate floor (e.g., `$20 USD/hr`).
   - Equity preference and prioritized benefits (Health insurance, PTO, Hardware stipend, Learning budget).
6. **Domains of Interest & Industry Dealbreakers:**
   - Target domains (GenAI/LLMs, RL, Computer Vision, Systems, MLOps, NLP).
   - Disallowed industries / toxic patterns (e.g. Crypto, unpaid overtime, 5 days/week onsite during semester).

### Step 3: Save & Bi-Directional Vault Sync

Click **"Save Preferences"** in the web UI header or submit a payload to the REST endpoint:
```http
POST /api/save HTTP/1.1
Content-Type: application/json
```

When saved:
1. Validates schema using [`preference_models.py`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/preference-manager/scripts/preference_models.py).
2. Updates [`001-background/preferences.json`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.json) with full data including availability grid.
3. Synchronizes flat YAML frontmatter to [`001-background/preferences.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.md).
   - **Obsidian Invariant:** Never outputs nested YAML dictionaries/objects.
   - **Tag Invariant:** Tags contain alphanumeric characters (e.g. `summer-2027`, never pure numbers).

### Step 4: Run AI Opportunity Audit

Audit all tracked opportunities against the latest preference parameters.

#### Option A: Via Web UI
Click the **"Save & Run AI Opportunity Audit"** button in the UI header. This triggers `POST /api/audit`, executes the audit engine, and returns a live modal summary with the generated report path.

#### Option B: Via Command Line
```powershell
.\.venv\Scripts\python.exe .agents/skills/preference-manager/scripts/audit_preferences.py
```

##### Audit CLI Flags:
- `--preferences` / `-p`: Path to preferences JSON file (default: `001-background/preferences.json`).
- `--opportunities` / `-o`: Path to opportunities database JSON (default: `004-work-opportunities/database/opportunities.json`).
- `--output` / `-out`: Path to output markdown report (default: `004-work-opportunities/opportunities-preference-audit.md`).

Example custom run:
```powershell
.\.venv\Scripts\python.exe .agents/skills/preference-manager/scripts/audit_preferences.py --preferences 001-background/preferences.json --opportunities 004-work-opportunities/database/opportunities.json --output 004-work-opportunities/opportunities-preference-audit.md
```

#### The 3-Tier Categorization Logic:
The engine analyzes each posting against Diego's active constraints and routes it into one of three deterministic categories:

1. **Direct Matches (`direct_matches`)**:
   - Opportunities with semester-compatible hours (`<= max_weekly_hours`, e.g. 20–30h/wk).
   - Based in Mexico or offering fully remote work arrangements.
   - Free of visa/relocation hurdles or caution flags.

2. **Caution or Summer (`caution_or_summer`)**:
   - Viable opportunities that require scheduling adjustments, international paperwork, or summer timing:
     - **Summer internships**: Role takes place during summer break (ideal for Summer 2027 cycle).
     - **Excess semester hours**: Workload (> max weekly hours, e.g. 40h/wk) exceeds semester bandwidth.
     - **Visa sponsorship required**: US J-1 sponsorship, Canadian co-op work permit, or international relocation needed.
     - **International remote**: Requires verifying W-8BEN contractor support vs US domestic payroll.
     - **Summer onsite**: Full-time onsite roles scheduled during summer break (exempt from hard disqualification via the Summer Onsite Guard).

3. **Disqualified (`disqualified`)**:
   - Postings violating absolute dealbreakers:
     - Hard status marks (`disqualified`, `ineligible`, `rejected`).
     - Blacklisted industries (e.g. Crypto, Web3, Blockchain).
     - Strict US citizenship or active security clearance requirements (with negation guards for "no citizenship required").
     - Inflexible 5 days/week onsite during the active semester.

#### Report Output:
Generates [`004-work-opportunities/opportunities-preference-audit.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/004-work-opportunities/opportunities-preference-audit.md) with Obsidian-compliant flat YAML frontmatter, executive metrics summary, categorized tables, and a dynamic action plan.

---

## Canary Rule & Agent Sentinel

> [!IMPORTANT]
> **Canary Invariant Rule**: Every user-facing response to Diego MUST start with his name: **Perea** (e.g. `Hello Perea, ...` or `Perea, ...`).
> This rule applies across all agent interactions, audit summaries, and tool feedback without exception.

---

## Verification & Test Suite

Verify that all components, models, and endpoints are healthy:

1. **Verify File Paths Exist:**
   - `.agents/skills/preference-manager/scripts/preference_server.py`
   - `.agents/skills/preference-manager/scripts/preference_models.py`
   - `.agents/skills/preference-manager/scripts/audit_preferences.py`
   - `.agents/skills/preference-manager/web/index.html`
   - `.agents/skills/preference-manager/web/style.css`
   - `.agents/skills/preference-manager/web/app.js`
   - `001-background/preferences.json`
   - `001-background/preferences.md`

2. **Run the Complete Unit Test Suite:**
   ```powershell
   .\.venv\Scripts\python.exe -m unittest discover -s tests
   ```
   *Expected outcome: All 20 tests pass with code 0 (`OK`).*

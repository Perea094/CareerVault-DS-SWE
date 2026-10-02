---
name: preference-manager
description: Manage, edit, and audit candidate career preferences, weekly availability grid, work modality rankings, compensation floors, and opportunity alignment scoring via an interactive survey web UI or CLI.
---

# preference-manager

Interactive survey web UI, dual-file persistence engine, and AI opportunity alignment auditor for managing candidate career preferences and active job-search constraints.

Maintains strict synchronization between the rich JSON schema ([`001-background/preferences.json`](001-background/preferences.json)) and Obsidian-compliant flat frontmatter Markdown ([`001-background/preferences.md`](001-background/preferences.md)), while scoring tracked opportunities against live constraints.

---

## When to Use & Triggering

Summon or trigger this skill whenever:
- Candidate needs to update weekly schedule, available hours, or semester course block commitments.
- Modality preferences change (e.g. Remote vs. Hybrid vs. Onsite priority order).
- Financial compensation floors (minimum hourly rate in USD) or benefits priorities are revised.
- Target domains (GenAI, RL, Vision, NLP, Systems) or dealbreakers (e.g. Crypto, unpaid overtime) are adjusted.
- An opportunity audit is required to filter and rank postings in [`004-work-opportunities/`](004-work-opportunities/) against active constraints.

**Do NOT use for**:
- Ingesting raw experiences or academic projects (use [`add-experience-curriculum`](.agents/skills/add-experience-curriculum/SKILL.md)).
- Scraping external job feeds (use [`opportunity-scout`](.agents/skills/opportunity-scout/SKILL.md)).
- Tailoring individual resumes/CVs (use [`tailored-cv`](.agents/skills/tailored-cv/SKILL.md)).

---

## Target Vault Paths & Key Components

- **Web Server & REST API:** [`.agents/skills/preference-manager/scripts/preference_server.py`](.agents/skills/preference-manager/scripts/preference_server.py)
- **Data Model & Sync Engine:** [`.agents/skills/preference-manager/scripts/preference_models.py`](.agents/skills/preference-manager/scripts/preference_models.py)
- **AI Opportunity Audit Script:** [`.agents/skills/preference-manager/scripts/audit_preferences.py`](.agents/skills/preference-manager/scripts/audit_preferences.py)
- **Web App Assets:**
  - HTML structure: [`.agents/skills/preference-manager/web/index.html`](.agents/skills/preference-manager/web/index.html)
  - Styling (glassmorphism/responsive): [`.agents/skills/preference-manager/web/style.css`](.agents/skills/preference-manager/web/style.css)
  - Interactive UI logic: [`.agents/skills/preference-manager/web/app.js`](.agents/skills/preference-manager/web/app.js)
- **Master Preference Ground Truth (JSON):** [`001-background/preferences.json`](001-background/preferences.json)
- **Obsidian Human-Readable Notes (MD):** [`001-background/preferences.md`](001-background/preferences.md)
- **Audited Opportunities Database:** [`004-work-opportunities/database/opportunities.json`](004-work-opportunities/database/opportunities.json)
- **Generated Audit Report:** [`004-work-opportunities/opportunities-preference-audit.md`](004-work-opportunities/opportunities-preference-audit.md)

---

## End-to-End Workflow Guide

### Step 1: Launch the Interactive Web Survey

Start the dedicated local preference server from terminal:

```powershell
python .agents/skills/preference-manager/scripts/preference_server.py --open
```

- **Default Port:** `8765` (customizable via `--port <PORT>`).
- **Browser:** The `--open` flag automatically opens the default web browser to `http://127.0.0.1:8765/`.
- If the browser does not open automatically, navigate to `http://127.0.0.1:8765/` manually.

### Step 2: Configure Career Preferences in the Web UI

The web UI guides the candidate through structured configuration cards:

1. **Work Modality Ranking:**
   - Drag-and-drop or use up/down reorder buttons to rank `Remote`, `Hybrid`, and `Onsite`.
2. **Weekly Availability & Schedule Grid:**
   - 7 days (Monday–Sunday) across 32 thirty-minute time blocks from 06:00 to 22:00 (06:00–06:30 through 21:30–22:00).
   - Click or drag-select cells to cycle through 3 slot states:
     - `available` (open for work/projects, adds 0.5 hrs (30 min) to weekly tally)
     - `classes` (academic coursework / commitments)
     - `busy` (personal blocks, study, or other commitments)
   - Real-time weekly available hours calculator (summing active `available` slots).
3. **Weekly Hours & Flexibility:**
   - Target range (e.g., `20-30` hours/week during semester, `40` max manageable).
   - Timezone overlap preferences and async/sync communication balance.
4. **Location & Visa Status:**
   - Base location (`City, Country`).
   - US work authorization (None / Needs sponsorship or international contractor agreement).
5. **Compensation & Benefits:**
   - Minimum hourly rate floor (e.g., `$20 USD/hr`).
   - Equity preference and prioritized benefits (Health insurance, PTO, Hardware stipend, Learning budget).
6. **Domains of Interest & Industry Dealbreakers:**
   - Target domains (GenAI/LLMs, RL, Computer Vision, Systems, MLOps, NLP).
   - Disallowed industries / patterns (e.g. Crypto, unpaid overtime, 5 days/week onsite during term).

### Step 3: Save & Bi-Directional Vault Sync

Click **"Save Preferences"** in the web UI header or submit a payload to the REST endpoint:
```http
POST /api/save HTTP/1.1
Content-Type: application/json
```

When saved:
1. Validates schema using [`preference_models.py`](.agents/skills/preference-manager/scripts/preference_models.py).
2. Updates [`001-background/preferences.json`](001-background/preferences.json) with full data including availability grid.
3. Synchronizes flat YAML frontmatter to [`001-background/preferences.md`](001-background/preferences.md).
   - **Obsidian Invariant:** Never outputs nested YAML dictionaries/objects.
   - **Tag Invariant:** Tags contain alphanumeric characters (e.g. `summer-2027`, never pure numbers).

### Step 4: Run AI Opportunity Audit

Audit all tracked opportunities against the latest preference parameters.

#### Option A: Via Web UI
Click the **"Save & Run AI Opportunity Audit"** button in the UI header. This triggers `POST /api/audit`, executes the audit engine, and returns a live modal summary with the generated report path.

#### Option B: Via Command Line
```powershell
python .agents/skills/preference-manager/scripts/audit_preferences.py
```

##### Audit CLI Flags:
- `--preferences` / `-p`: Path to preferences JSON file (default: `001-background/preferences.json`).
- `--opportunities` / `-o`: Path to opportunities database JSON (default: `004-work-opportunities/database/opportunities.json`).
- `--output` / `-out`: Path to output markdown report (default: `004-work-opportunities/opportunities-preference-audit.md`).

#### The 3-Tier Categorization Logic:
The engine analyzes each posting against active constraints and routes it into one of three deterministic categories:

1. **Direct Matches (`direct_matches`)**:
   - Opportunities with term-compatible hours (`<= max_weekly_hours`, e.g. 20–30h/wk).
   - Based locally or offering fully remote work arrangements.
   - Free of visa/relocation hurdles or caution flags.

2. **Caution or Summer (`caution_or_summer`)**:
   - Viable opportunities that require scheduling adjustments, international paperwork, or summer timing:
     - **Summer internships**: Role takes place during summer break (ideal for summer cycles).
     - **Excess term hours**: Workload (> max weekly hours, e.g. 40h/wk) exceeds semester bandwidth.
     - **Visa sponsorship required**: Sponsorship or international relocation needed.
     - **Summer onsite**: Full-time onsite roles scheduled during summer break.

3. **Disqualified (`disqualified`)**:
   - Postings violating absolute dealbreakers:
     - Hard status marks (`disqualified`, `ineligible`, `rejected`).
     - Blacklisted industries (e.g. Crypto, Web3, Blockchain).
     - Strict citizenship or security clearance requirements.
     - Inflexible 5 days/week onsite during active academic term.

#### Report Output:
Generates [`004-work-opportunities/opportunities-preference-audit.md`](004-work-opportunities/opportunities-preference-audit.md) with Obsidian-compliant flat YAML frontmatter, executive metrics summary, categorized tables, and a dynamic action plan.

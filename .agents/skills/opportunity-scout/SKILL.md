---
name: opportunity-scout
description: Automated daily scout and recruiter evaluation for tech internships, co-ops, and new grad roles across 19 GitHub repositories and feeds (SpeedyApply, SimplifyJobs, Jobright, Vanshb03, Proyecto Nutria, zshah101, SuryaHarikrishnan, Negarprh, DereC4, Mehek), synchronizing the central opportunities database and monthly audit notes.
---

# opportunity-scout

Automates the ingestion, multi-source deduplication, and senior technical recruitment evaluation of software engineering, AI/ML, data science, and quant job postings.

## Target Vault Paths
- **Scanner Script:** `004-work-opportunities/scripts/scan_opportunities.py`
- **Feed Configuration:** `004-work-opportunities/scripts/sources.json`
- **Pending Candidates:** `004-work-opportunities/database/pending_scan.json`
- **Central Database (JSON):** `004-work-opportunities/database/opportunities.json`
- **Central Database (CSV):** `004-work-opportunities/database/opportunities.csv`
- **Monthly Audit Notes:** `004-work-opportunities/opportunities-audit-YYYY-MM.md`
- **Dynamic Constraints:** `001-background/preferences.md`
- **Verified Background Evidence:** `001-background/`

---

## The 4-Step Execution Workflow

### Step 1: Run Ingestion & Pre-Filtering
For daily monitoring:
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --verify-links
```

For domain-specific scoping (e.g. Data Science):
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --role "data scientist, machine learning" --verify-links
```

For initial vault onboarding / first audit:
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --audit-mode
```
This queries 19 active feeds across SpeedyApply, SimplifyJobs, Jobright, Vanshb03, Proyecto Nutria (Mexico), zshah101, SuryaHarikrishnan, Negarprh (Canada), DereC4 (Trendshift #99924), and Mehek/Litos, deduplicates against `opportunities.json`, filters out hard deal-breakers (crypto, strict PhD gates, US citizenship required), and exports the top priority batch to `004-work-opportunities/database/pending_scan.json`.

### Step 2: Check Scan Results
Inspect `004-work-opportunities/database/pending_scan.json`:
- If empty (`[]`): Report that all feeds are up-to-date and 0 new opportunities were found today. Conclude execution.
- If new candidates are present: Proceed to Step 3.

### Step 3: Senior Recruiter Evaluation (via `expert-recruiter`)
For each opportunity in `pending_scan.json`:
1. **Dynamic Constraints Check**: Read `001-background/preferences.md` to ensure compliance with active work arrangements, location/visa rules, hours (target weekly hours), and compensation floor.
2. **Ground Truth CV Highlights**: Map 3–4 bullet points directly to verified background assets in `001-background/`.
3. **Realistic Success Ratio**: Assign a concrete percentage range (e.g. `85% - 90%` for Tier 1 local/remote, `40% - 50%` for high-competition sponsors) with recruiter justification.
4. **Key Considerations**: Note legal requirements (visa sponsorship, local entity), graduation alignment, and schedule compatibility.
5. **Pros & Cons**: Assess brand prestige, compensation, remote flexibility vs commute, and risks.
6. **Skills Gap Analysis**: Pinpoint missing technical keywords or tools and prescribe exact bridging actions.

### Step 4: Vault Synchronization & Reporting
1. **Append to JSON Database**: Add the structured records to `004-work-opportunities/database/opportunities.json`.
2. **Sync CSV**: Regenerate `004-work-opportunities/database/opportunities.csv`.
3. **Update Monthly Audit Note**: Append or update `004-work-opportunities/opportunities-audit-YYYY-MM.md` (e.g., `opportunities-audit-2026-10.md`), updating the Priority Matrix table and adding the opportunity sections.
   - **Obsidian Frontmatter Invariants**:
     - **Valid String Tags Only**: Never use pure numbers for tags (e.g., use `summer-2027` or `cycle-2027`, NEVER `2027`). Obsidian requires at least one letter in every tag; pure numeric tags cause Obsidian property validation warnings (`⚠️`).
     - **Flat Properties Only**: Never write nested YAML objects/dictionaries (e.g., use `candidate_profile_ref: "001-background/preferences.md"`, never nested `candidate_profile: {degree: ...}` which Obsidian flags with an unsupported type `?`).
4. **User Briefing**: Deliver a 3-bullet summary highlighting newly discovered Tier 1 and Remote Part-Time roles.

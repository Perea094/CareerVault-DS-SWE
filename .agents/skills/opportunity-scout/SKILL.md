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
For turnkey scanning and automated end-to-end synchronization:
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --audit-mode --sync
```
*Note on `--sync`*: The `--sync` flag automates the entire pipeline by enriching candidates with the complete 18-attribute senior recruiter schema, updating `opportunities.json`, regenerating `opportunities.csv`, and writing/updating the monthly audit note (`opportunities-audit-YYYY-MM.md`).

For daily incremental monitoring with link verification:
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --verify-links --sync
```

For domain-specific scoping (e.g. Data Science):
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --role "data scientist, machine learning" --verify-links --sync
```

For initial vault onboarding / first audit:
```powershell
python 004-work-opportunities/scripts/scan_opportunities.py --audit-mode --sync
```
This queries 19 active feeds across SpeedyApply, SimplifyJobs, Jobright, Vanshb03, Proyecto Nutria (Mexico), zshah101, SuryaHarikrishnan, Negarprh (Canada), DereC4 (Trendshift #99924), and Mehek/Litos, deduplicates against `opportunities.json`, filters out hard deal-breakers (crypto, strict PhD gates, US citizenship required), and exports new candidates to `004-work-opportunities/database/pending_scan.json` (and automatically synchronizes them when `--sync` is passed).

### Step 2: Check Scan Results
Inspect `004-work-opportunities/database/pending_scan.json`:
- If empty (`[]`): Report that all feeds are up-to-date and 0 new opportunities were found today. Conclude execution.
- If new candidates are present:
  - If `--sync` was executed, candidates are already ingested into `opportunities.json`, `opportunities.csv`, and the monthly audit note. Proceed directly to Step 4 for briefing delivery.
  - If `--sync` was not passed, evaluate candidates in Step 3 and execute Step 4 synchronization.

### Step 3: Senior Recruiter Evaluation (via `expert-recruiter`) & 5-Tier Taxonomy
Every opportunity is evaluated and categorized according to the official **5-Tier Alignment Taxonomy**:
- **Tier 1: Candidate Domestic / Home Market (Direct Legal Match)** [Score: 90-95]
  - Roles based in candidate's home country/jurisdiction (e.g., Mexico) or where direct legal work authorization exists without visa friction.
- **Tier 2: Remote & Flexible Opportunities** [Score: 85]
  - Globally remote, Americas-friendly timezone, or part-time flexible student roles compatible with active academic commitments.
- **Tier 3: Elite Target Hubs (Visa Sponsorship Track)** [Score: 65]
  - US/Global elite tech companies, H-1B / J-1 / TN visa sponsors, FAANG/MAMAA, quant funds, and enterprise scale employers with established immigration sponsorship pipelines.
- **Tier 4: Canadian Co-op & International Hubs** [Score: 75]
  - Canada, LATAM international hubs, Europe, or UK positions with established exchange, work-permit, or international student co-op tracks.
- **Tier 5: General Domestic (Unverified Sponsorship)** [Score: 45]
  - General US domestic in-person or non-remote positions without verified visa sponsorship track records. High screening risk for international candidates.

For each evaluated opportunity:
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
4. **User Briefing & Strict Link Integrity**: Deliver a concise executive briefing highlighting newly discovered Tier 1 and Remote Part-Time roles, accompanied by a curated opportunities table with mandatory columns:
   `| Company | Role | Tier & Work Style | Est. Pass Ratio | Key Recruiter Insight | Link |`
   - **Strict Link Integrity Invariant**:
     - **MANDATORY**: Never construct, guess, or synthesize job URLs from memory.
     - All markdown links in the chat briefing table MUST be extracted verbatim from `apply_url` in `004-work-opportunities/database/opportunities.json` or live HTTP verified.
     - **Cloudflare / Anti-Bot Protected Portals**: Document that Cloudflare-protected corporate portals (like Citadel, Workday, Taleo) return HTTP 403 Forbidden to automated scripts or scrapers but resolve normally in standard user web browsers. For these roles, provide both the direct corporate portal link and aggregator mirrors (e.g., SimplifyJobs / Jobright / GitHub commit link) when available so the candidate can apply seamlessly.


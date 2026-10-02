# Opportunities Database & Triage Registry

## 1. Overview
This database serves as the structured registry for all evaluated job, internship, and co-op opportunities. It bridges the raw scrape feeds from GitHub curation repositories (e.g. `2027-AI-College-Jobs` and `2027-SWE-College-Jobs`) with the candidate profile and ground truth constraints in `001-background/preferences.md`.

- **JSON Master File:** [`004-work-opportunities/database/opportunities.json`](opportunities.json)
- **Archived Registry:** [`004-work-opportunities/database/archived_opportunities.json`](archived_opportunities.json)
- **CSV Export:** [`004-work-opportunities/database/opportunities.csv`](opportunities.csv)

---

## 2. Candidate Constraints & Dynamic Baseline
All candidate evaluation criteria must dynamically respect [`001-background/preferences.md`](../../001-background/preferences.md).

> [!NOTE] Dynamic Source of Truth
> Never duplicate or hardcode evaluation rules or static constraints here. Always inspect `001-background/preferences.md` directly at runtime for current career goals, degree standing, work arrangements, location & visa constraints, compensation floors, domain interests, and dealbreakers. When preferences are updated in the future, all downstream opportunity triaging and database records dynamically adapt to reflect those changes.

---

## 3. Database Schema Reference

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique slug identifier (e.g., `opp-01-salesforce-ai-builder-intern-mexico`). |
| `numeric_id` | integer | Sequential tracking index. |
| `company` | string | Employer or sponsoring enterprise name. |
| `role` | string | Exact title of the position. |
| `tier` | string | Stratified priority bucket (`Tier 1: Mexico/LATAM`, `Tier 2: Remote Part-Time`, `Tier 3: Elite US Summer`, `Tier 4: Canadian Co-op / Int'l`). |
| `location` | string | Geographic location and work style (Remote, Hybrid, Onsite). |
| `work_arrangement` | string | Term duration and schedule type (e.g. Part-time, Summer 2027, 4-Mo Co-op). |
| `hours_per_week` | string | Estimated hours required (`20-30` or `40`). |
| `compensation` | string | Hourly pay, stipend, or standard corporate rate. |
| `realistic_success_ratio` | string | Recruiter screening pass probability range (e.g., `85% - 90%`). |
| `success_ratio_min` / `max` | float | Decimal bounds (`0.85`, `0.90`) for numerical querying and sorting. |
| `success_ratio_justification` | string | Grounded recruiter rationale explaining why this ratio was assigned. |
| `urgency` | string | Time-sensitivity flag (e.g., `⚠️ URGENT: Closes Sep 21!`, `High (Posted 1d ago)`). |
| `strategic_action` | string | Next immediate operational step (e.g., `Immediate Apply (Tier 1)`, `Apply via Tec Convenio`). |
| `source_repo` | string | Upstream repository URL where the job was discovered. |
| `apply_url` | string | Direct portal URL to submit application. |
| `file_reference` | string | Local HTML dossier path under `004-work-opportunities/opportunities/`. |
| `vault_note` | string | Path to dedicated Markdown note under `004-work-opportunities/eligible/` if created. |
| `status` | string | Vault eligibility status (`eligible`, `non-eligible`, `archived`). |
| `application_status` | string | Pipeline lifecycle state (`pending_tailoring`, `ready_to_apply`, `applied`, `interviewing`, `rejected`, `offer`). |
| `key_points_to_highlight` | array[string] | Tailored bullet recommendations mapped directly to projects in `001-background/`. |
| `key_considerations` | array[string] | University agreements, visa terms, course schedules, or required documents. |
| `pros` | array[string] | Strategic career advantages. |
| `cons` | array[string] | Trade-offs, risks, or schedule conflicts. |
| `missing_or_bridge_skills` | array[string] | Explicit skill gaps and the recommended bridging action. |
| `date_identified` | string | Date when first discovered (`YYYY-MM-DD`). |
| `last_audited` | string | Date when last re-evaluated (`YYYY-MM-DD`). |

---

## 4. Stratified Priority Tiers

1. **Tier 1: Maximum Viability — Mexico & LATAM (Direct Legal Match & Zero Visa Barrier)**
   - *Target:* Roles based in Mexico City / Querétaro / Hybrid with Mexican legal entities.
   - *Fit:* 80% – 90% pass rate. Perfect alignment with university enrollment and legal eligibility.
2. **Tier 2: High Viability — Part-Time & Fully Remote AI / Data Roles**
   - *Target:* Remote roles allowing 20–30 hours/week or independent contractor status (W-8BEN).
   - *Fit:* 60% – 80% pass rate. Compatible with morning university lecture schedules.
3. **Tier 3: Elite US Summer 2027 Programs (Top Sponsoring Tech & Quant)**
   - *Target:* Highly selective US summer internships with guaranteed J-1 exchange visa sponsorship (Figma, Adobe, Jane Street, Citadel).
   - *Fit:* 15% – 50% pass rate. High compensation (\$55 – \$125/hr); requires rigorous algorithmic/math screening.
4. **Tier 4: Canadian AI Co-op & International Innovation Hubs**
   - *Target:* 4-to-6 month international co-ops (Toronto, Ottawa, Paris, London) offering work visas (Capital One Canada, EQ Bank, Ciena, Kinaxis, Mistral AI).
   - *Fit:* 25% – 55% pass rate. May require coordinating study leaves or remote semester credit with Tec de Monterrey.

---

## 5. Daily Scheduler Automation Lifecycle

```mermaid
flowchart TD
    A["Daily Cron / Scheduler Trigger"] --> B["Fetch SpeedyApply Repos (AI & SWE College Jobs)"]
    B --> C["Filter Raw Postings (Age <= 7d, Undergrad Eligible)"]
    C --> D["Deduplicate vs database/opportunities.json (by URL / Company+Role)"]
    D --> E["Recruiter Evaluation vs 001-background/preferences.md & 001-background/"]
    E --> F["Formulate Key Points, Success Ratio, Pros/Cons, Missing Skills"]
    F --> G["Append / Update opportunities-audit-YYYY-MM.md"]
    F --> H["Update database/opportunities.json & database/opportunities.csv"]
    H --> I["Notify Candidate with High-Priority Matches (Tier 1 & Remote)"]
```

# Unified Opportunities Scanner Architecture

This subsystem provides a modular, multi-source ingestion engine for college internship, co-op, and new grad tech opportunities across GitHub aggregation ecosystems.

---

## 1. Monitored Repositories & Feeds (`sources.json`)

The scanner monitors **19 high-volume feeds** across seven community aggregation ecosystems:

| Ecosystem | Feed ID | Focus | Format / Parser | Upstream URL |
| :--- | :--- | :--- | :--- | :--- |
| **SpeedyApply** | `speedyapply-ai-usa` | AI / ML (USA) | Markdown Table (`speedyapply`) | [2027-AI-College-Jobs](https://github.com/speedyapply/2027-AI-College-Jobs) |
| **SpeedyApply** | `speedyapply-ai-intl` | AI / ML (International) | Markdown Table (`speedyapply`) | [INTERN_INTL.md](https://raw.githubusercontent.com/speedyapply/2027-AI-College-Jobs/main/INTERN_INTL.md) |
| **SpeedyApply** | `speedyapply-swe-usa` | Software Engineering (USA) | Markdown Table (`speedyapply`) | [2027-SWE-College-Jobs](https://github.com/speedyapply/2027-SWE-College-Jobs) |
| **SpeedyApply** | `speedyapply-swe-intl` | Software Engineering (Int'l) | Markdown Table (`speedyapply`) | [INTERN_INTL.md](https://raw.githubusercontent.com/speedyapply/2027-SWE-College-Jobs/main/INTERN_INTL.md) |
| **SimplifyJobs** | `simplify-summer-2027` | Summer 2027 Internships | HTML Table (`simplify`) | [Summer2027-Internships](https://github.com/SimplifyJobs/Summer2027-Internships) |
| **SimplifyJobs** | `simplify-off-season-2027` | Winter/Co-op 2027 | HTML Table (`simplify`) | [README-Off-Season.md](https://github.com/SimplifyJobs/Summer2027-Internships/blob/dev/README-Off-Season.md) |
| **SimplifyJobs** | `simplify-new-grad` | New Grad Full-Time | HTML Table (`simplify`) | [New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) |
| **Jobright-ai** | `jobright-data-analysis-new-grad` | Data Analysis / Science | Markdown Table (`jobright`) | [2026-Data-Analysis-New-Grad](https://github.com/jobright-ai/2026-Data-Analysis-New-Grad) |
| **Jobright-ai** | `jobright-swe-intern` | SWE Internships | Markdown Table (`jobright`) | [2026-Software-Engineer-Internship](https://github.com/jobright-ai/2026-Software-Engineer-Internship) |
| **Jobright-ai** | `jobright-swe-new-grad` | SWE New Grad | Markdown Table (`jobright`) | [2026-Software-Engineer-New-Grad](https://github.com/jobright-ai/2026-Software-Engineer-New-Grad) |
| **Jobright-ai** | `jobright-gen-intern` | General Tech Internships | Markdown Table (`jobright`) | [2026-Internship](https://github.com/jobright-ai/2026-Internship) |
| **Vanshb03** | `vanshb03-summer-2027` | Tech / Internships | Markdown Table (`speedyapply`) | [Summer2027-Internships](https://github.com/vanshb03/Summer2027-Internships) |
| **Proyecto Nutria** | `proyecto-nutria-mx` | Mexico Tech Internships | Markdown Table (`speedyapply`) | [MX-Internships](https://github.com/Proyecto-Nutria/MX-Internships) |
| **zshah101** | `zshah101-automated-2027` | Automated Bot Tracker | Direct JSON (`zshah`) | [Automated-List](https://github.com/zshah101/Automated-List-Of-Summer-2027-and-Fall-2026-Tech-Internships) |
| **SuryaHarikrishnan** | `surya-tracker-2027` | Aggregated 2027 Tracker | Direct JSON (`surya`) | [2027-internship-tracker](https://github.com/SuryaHarikrishnan/2027-internship-tracker) |
| **Negarprh** | `negarprh-canada-2027` | Canadian Tech Internships | Markdown Table (`negarprh`) | [Canadian-Tech-Internships-2027](https://github.com/negarprh/Canadian-Tech-Internships-2027) |
| **DereC4** | `derec4-tech-2027` | Tech Internships (Trendshift #99924) | Markdown Table (`derec4`) | [internships-and-newgrad](https://github.com/DereC4/internships-and-newgrad) |
| **Mehek / Litos** | `mehek-summer-2027-swe` | SWE Internships | Markdown Table (`mehek`) | [Summer2027-Internships](https://github.com/mehek-builds/Summer2027-Internships) |
| **Mehek / Litos** | `mehek-summer-2027-ai` | AI / Data Internships | Markdown Table (`mehek`) | [Summer2027-Internships](https://github.com/mehek-builds/Summer2027-Internships) |

---

## 2. Modular Parser Architecture (`adapters/`)

1. **`speedyapply_adapter.py`**: Parses GitHub-flavored Markdown tables for SpeedyApply, Vanshb03, and Proyecto Nutria.
2. **`jobright_adapter.py`**: Parses Jobright Markdown tables with work model and date normalization.
3. **`simplify_adapter.py`**: Parses HTML tables with company inheritance and emoji legal/sponsorship badge extraction.
4. **`zshah_adapter.py`**: Parses real-time automated bot JSON (`data/jobs.json`) with direct J-1/H-1B visa sponsorship flags.
5. **`surya_adapter.py`**: Ingests multi-source JSON database (`data/listings.json`) with active status filtering.
6. **`table_adapter.py`**: Modular Markdown table adapter handling Negarprh (Canadian co-ops), DereC4 (3,000+ line repository tracked by Trendshift), Mehek/Litos (direct ATS links and salary rates), and LorenzoLaCorte (European hub).

---

## 3. Dynamic Worldwide Viability & Triage Engine

Every job posting is dynamically evaluated against the candidate's active constraints in [`001-background/preferences.json`](../../001-background/preferences.json) (with fallback to [`001-background/preferences.md`](../../001-background/preferences.md)):
- **Candidate Context Integration**:
  - **Home Location (`current_location`)**: Dynamically resolves the candidate's home country and metropolitan region anywhere worldwide (e.g., Mexico, Canada, United States, United Kingdom, Germany, Brazil, India, etc.).
  - **Work Authorization (`us_work_authorization`)**: Recognizes domestic authorization (Citizen, Permanent Resident) versus international sponsorship requirements (None, J-1, H-1B, TN). Domestic authorized candidates receive Tier 1 status for home country roles without visa penalties.
  - **Disallowed Industries (`industries_to_avoid`)**: Dynamically filters excluded sectors (Crypto, Web3, Gambling, etc.).
- **Hard Disqualifiers**:
  - `sponsorship_notes` containing "US Citizenship Required" or "No Visa Sponsorship" on US onsite roles (when candidate lacks US work authorization).
  - Strict PhD-only or Master's-only requisitions (unless undergraduate applicants are explicitly welcome).
  - Excluded industries configured in `preferences.json` (Crypto, Web3, Blockchain, etc.).
  - Missing application URLs.
- **Stratified Priority Tiers**:
  - **Tier 1 (Domestic / Home Market)**: Direct legal match in the candidate's home country/region with zero visa friction. (Score: 95)
  - **Tier 2 (Remote Part-Time & Flexible)**: Global remote roles matching candidate schedule and target hours. (Score: 85)
  - **Tier 3 (Elite Sponsoring Programs / Target Hubs)**: Top tech/quant firms sponsoring J-1/H-1B visas (Figma, Adobe, Jane Street, Citadel, etc.), or domestic elite programs if authorized. (Score: 65)
  - **Tier 4 (Global Co-op & International Hubs)**: International co-op terms and innovation hubs offering exchange permits or bilateral agreements. (Score: 50–75)

---

## 4. CLI Usage

Run the scanner directly from the command line:

```powershell
# Default scan (Max age: 7 days, Top 10 batch)
python 004-work-opportunities/scripts/scan_opportunities.py

# Custom lookback window (e.g. 3 days) and batch limit
python 004-work-opportunities/scripts/scan_opportunities.py --days 3 --limit 5

# Scan only a specific feed
python 004-work-opportunities/scripts/scan_opportunities.py --source simplify-summer-2027

# Scan without limiting candidate batch
python 004-work-opportunities/scripts/scan_opportunities.py --all
```

Outputs are automatically deduplicated against [`004-work-opportunities/database/opportunities.json`](../database/opportunities.json) and exported to [`004-work-opportunities/database/pending_scan.json`](../database/pending_scan.json).

---

## 5. Pruning & Archival Engine (`prune_opportunities.py`)

Maintains database freshness by sweeping expired, dead, or passed opportunities into [`004-work-opportunities/database/archived_opportunities.json`](../database/archived_opportunities.json) while preserving deduplication memory:

```powershell
# Probe ATS URLs concurrently to detect 404s and closed positions (Dry run preview)
python 004-work-opportunities/scripts/prune_opportunities.py --check-links --dry-run

# Commit dead link archival (synchronizes JSON, CSV, and root mirror)
python 004-work-opportunities/scripts/prune_opportunities.py --check-links

# Sweep opportunities older than 45 days
python 004-work-opportunities/scripts/prune_opportunities.py --older-than 45

# Sweep manually passed, rejected, or closed roles
python 004-work-opportunities/scripts/prune_opportunities.py --archive-status passed,rejected,closed

# Shortcut: mark a specific ID as passed and archive it
python 004-work-opportunities/scripts/prune_opportunities.py --mark-passed opp-01-example-intern-id

# List all archived opportunities
python 004-work-opportunities/scripts/prune_opportunities.py --list-archived
```


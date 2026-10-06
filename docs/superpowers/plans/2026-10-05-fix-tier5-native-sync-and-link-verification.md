# Tier 5 Taxonomy, Native Turnkey Sync Pipeline, and Link Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Establish a distinct "Tier 5: General Domestic (Unverified Sponsorship)" category to resolve the Tier 3 collision, build a turnkey native `--sync` database pipeline bridging scanned opportunities to the 18-property recruiter schema and monthly audit reports without scratch scripts, and enforce end-to-end link verification to eliminate dead and synthetic URLs.

**Architecture:** 
1. Update `scan_opportunities.py` scoring logic so non-remote US opportunities without top sponsor status receive score 45 and `"Tier 5: General Domestic (Unverified Sponsorship)"`. Migrate existing records in `opportunities.json`, `opportunities.csv`, `pending_scan.json`, and monthly audit notes.
2. Build a native, modular synchronization module (`004-work-opportunities/scripts/sync_opportunities.py`) integrated into `scan_opportunities.py --sync` that validates links, generates the full 18-attribute senior recruiter evaluation schema, updates `opportunities.json`, regenerates `opportunities.csv`, and writes `opportunities-audit-YYYY-MM.md`.
3. Prune confirmed closed opportunities (e.g. Keysight Technologies) to `archived_opportunities.json` and update `.agents/skills/opportunity-scout/SKILL.md` to mandate ground-truth link referencing from `opportunities.json["apply_url"]`.

**Tech Stack:** Python 3.8+, `argparse`, `unittest`, `concurrent.futures`, `json`, `csv`, `urllib.request`.

---

## File Structure Map

- **Create:**
  - `004-work-opportunities/scripts/sync_opportunities.py`: Core synchronization engine providing `enrich_candidate()`, `sync_database()`, and `generate_monthly_audit()`.
  - `tests/test_sync_opportunities.py`: Unit tests for candidate enrichment, schema completeness (all 18 fields), database merging, CSV generation, and monthly audit markdown formatting.

- **Modify:**
  - `004-work-opportunities/scripts/scan_opportunities.py`:
    - Update `calculate_alignment_score` to assign `"Tier 5: General Domestic (Unverified Sponsorship)"` (score 45) for unverified domestic US opportunities.
    - Add `--sync` CLI flag in `main()` to automatically invoke `sync_opportunities.sync_database()` and `sync_opportunities.generate_monthly_audit()` on verified candidates.
  - `004-work-opportunities/database/opportunities.json`:
    - Migrate 17 occurrences of `"Tier 3: General US Opportunity"` to `"Tier 5: General Domestic (Unverified Sponsorship)"`.
    - Archive closed Keysight Technologies opportunity.
  - `004-work-opportunities/database/opportunities.csv`:
    - Update records to reflect Tier 5 and archive pruning.
  - `004-work-opportunities/database/pending_scan.json`:
    - Update `"Tier 3: General US Opportunity"` entries to `"Tier 5: General Domestic (Unverified Sponsorship)"`.
  - `004-work-opportunities/opportunities-audit-2026-10.md`:
    - Update audit tables, tier distributions, and links.
  - `.agents/skills/opportunity-scout/SKILL.md`:
    - Update Step 1, 3, 4 with the 5-Tier taxonomy, `--sync` flag workflow, and strict link extraction rules.
  - `tests/test_scan_opportunities.py`:
    - Add test cases verifying Tier 5 labeling and CLI `--sync` argument.

---

### Task 1: Update Alignment Scoring to Tier 5 and Migrate Database

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py:384-392`
- Test: `tests/test_scan_opportunities.py`
- Modify: `004-work-opportunities/database/opportunities.json`
- Modify: `004-work-opportunities/database/pending_scan.json`
- Modify: `004-work-opportunities/database/opportunities.csv`

- [x] **Step 1: Write failing unit test for Tier 5 scoring**

Add test to `tests/test_scan_opportunities.py`:
```python
    def test_general_us_role_assigned_tier_5(self):
        profile = CandidateProfile(
            name="Diego Perea",
            location="Querétaro, Mexico",
            work_authorization="None"
        )
        opp_us_general = {
            "company": "The New York Mets",
            "role": "Intern - Data Science",
            "location": "Citi Field, Queens, NY, United States",
            "apply_url": "https://example.com/mets"
        }
        score, tier = score_and_tier(opp_us_general, profile)
        self.assertEqual(score, 45)
        self.assertEqual(tier, "Tier 5: General Domestic (Unverified Sponsorship)")
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_scan_opportunities.py -k test_general_us_role_assigned_tier_5`
Expected: FAIL (`AssertionError: 'Tier 3: General US Opportunity' != 'Tier 5: General Domestic (Unverified Sponsorship)'`)

- [x] **Step 3: Update `scan_opportunities.py` to assign Tier 5**

In `004-work-opportunities/scripts/scan_opportunities.py#L384-L389`:
```python
    # 6. General US Roles (Domestic in-person without verified top sponsor status)
    if any(k in loc for k in ["united states", "usa"]) or re.search(r'\b(us|u\.s\.)\b', loc) or "usa" in item.get("source_id", ""):
        if profile.is_us_authorized:
            return 90, "Tier 1: United States (Direct Legal Match)"
        return 45, "Tier 5: General Domestic (Unverified Sponsorship)"
```

- [x] **Step 4: Run unit test to verify it passes**

Run: `python -m unittest tests/test_scan_opportunities.py -k test_general_us_role_assigned_tier_5`
Expected: PASS

- [x] **Step 5: Migrate existing records in `opportunities.json`, `pending_scan.json`, and `opportunities.csv`**

Run python migration script to replace `"Tier 3: General US Opportunity"` with `"Tier 5: General Domestic (Unverified Sponsorship)"` across `opportunities.json`, `pending_scan.json`, and regenerate `opportunities.csv`.

- [x] **Step 6: Commit changes**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py 004-work-opportunities/database/ tests/test_scan_opportunities.py
git commit -m "feat(opportunities): formalize Tier 5 General Domestic taxonomy and migrate database"
```

---

### Task 2: Build Native Turnkey Sync Module (`sync_opportunities.py`)

**Files:**
- Create: `004-work-opportunities/scripts/sync_opportunities.py`
- Create: `tests/test_sync_opportunities.py`

- [x] **Step 1: Write failing tests for candidate enrichment and database sync**

In `tests/test_sync_opportunities.py`:
```python
import unittest
import json
import os
import tempfile
import sys

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import sync_opportunities
from scan_opportunities import CandidateProfile

class TestSyncOpportunities(unittest.TestCase):
    def setUp(self):
        self.profile = CandidateProfile(
            name="Diego Perea",
            location="Querétaro, Mexico",
            work_authorization="None"
        )

    def test_enrich_candidate_has_all_18_fields(self):
        raw_opp = {
            "company": "Amgen",
            "role": "Undergrad Intern – Data Scientist",
            "tier_category": "Tier 2: Remote & Flexible Opportunities",
            "location": "Remote, United States",
            "position_type": "Internship / Co-op",
            "hours": "20-40 hrs/week (Flexible/Term-dependent)",
            "compensation": "$40 - $55/hr",
            "apply_url": "https://jobright.ai/jobs/info/6a454d19372c01f6cd712c96",
            "source": "Jobright 2026 Data Analysis New Grad"
        }
        enriched = sync_opportunities.enrich_candidate(raw_opp, self.profile, numeric_id=1)
        expected_keys = [
            "id", "numeric_id", "company", "role", "tier", "location", "work_arrangement",
            "hours_per_week", "compensation", "realistic_success_ratio", "success_ratio_min",
            "success_ratio_max", "success_ratio_justification", "urgency", "strategic_action",
            "source_repo", "apply_url", "vault_note", "status", "application_status",
            "key_points_to_highlight", "key_considerations", "missing_or_bridge_skills"
        ]
        for key in expected_keys:
            self.assertIn(key, enriched, f"Missing key: {key}")
        self.assertEqual(enriched["numeric_id"], 1)
        self.assertEqual(enriched["status"], "eligible")
        self.assertEqual(enriched["application_status"], "wishlist")

    def test_sync_database_merges_and_avoids_duplicates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "opportunities.json")
            csv_path = os.path.join(tmpdir, "opportunities.csv")
            initial_db = {
                "opportunities": [
                    {"id": "opp-01-amgen", "numeric_id": 1, "company": "Amgen", "role": "Data Scientist Intern", "apply_url": "https://jobright.ai/apply1"}
                ]
            }
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(initial_db, f)

            new_candidates = [
                {"company": "Amgen", "role": "Data Scientist Intern", "apply_url": "https://jobright.ai/apply1"}, # duplicate
                {"company": "Microsoft", "role": "Data Scientist Intern", "apply_url": "https://careers.microsoft.com/apply2"} # new
            ]
            added_count = sync_opportunities.sync_database(new_candidates, db_path, csv_path, self.profile)
            self.assertEqual(added_count, 1)

            with open(db_path, "r", encoding="utf-8") as f:
                updated = json.load(f)
            self.assertEqual(len(updated["opportunities"]), 2)
            self.assertEqual(updated["opportunities"][1]["numeric_id"], 2)
            self.assertTrue(os.path.exists(csv_path))
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_sync_opportunities.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'sync_opportunities'`

- [x] **Step 3: Implement `sync_opportunities.py`**

Create `004-work-opportunities/scripts/sync_opportunities.py`:
- `slugify(company, role)`: Generate standardized id `opp-XX-company-role`.
- `estimate_success_ratio(tier, profile, role, loc)`: Derive realistic pass ratio and justification.
- `enrich_candidate(cand, profile, numeric_id)`: Generate complete 18-property dictionary matching schema in `opportunities.json`.
- `sync_database(candidates, db_path, csv_path, profile, verify_links=True)`: Load database, deduplicate by `apply_url` and normalized company/role, assign sequential IDs, persist JSON, and invoke `prune_opportunities.sync_csv()`.
- `generate_monthly_audit(opportunities, output_path, month_str, profile)`: Generate markdown table, KPI distribution, and senior recruiter recommendations.

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_sync_opportunities.py`
Expected: PASS

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/scripts/sync_opportunities.py tests/test_sync_opportunities.py
git commit -m "feat(opportunities): implement turnkey sync_opportunities module"
```

---

### Task 3: Integrate Native `--sync` into `scan_opportunities.py`

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py`
- Test: `tests/test_scan_opportunities.py`

- [x] **Step 1: Write test for `--sync` flag in `scan_opportunities.py`**

In `tests/test_scan_opportunities.py`:
```python
    @patch("sync_opportunities.sync_database")
    @patch("sync_opportunities.generate_monthly_audit")
    def test_scan_opportunities_sync_flag(self, mock_audit, mock_sync):
        mock_sync.return_value = 5
        test_args = ["scan_opportunities.py", "--limit", "1", "--sync"]
        with patch.object(sys, "argv", test_args):
            with patch("scan_opportunities.fetch_all_sources", return_value=[{"company": "Test", "role": "Intern", "location": "Remote", "apply_url": "https://example.com/test"}]):
                scan_opportunities.main()
        mock_sync.assert_called_once()
        mock_audit.assert_called_once()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_scan_opportunities.py -k test_scan_opportunities_sync_flag`
Expected: FAIL (unrecognized argument `--sync`)

- [x] **Step 3: Implement `--sync` in `scan_opportunities.py` CLI**

In `scan_opportunities.py`:
1. Import `sync_opportunities`.
2. Add argument to `parser`:
```python
parser.add_argument("--sync", action="store_true", help="Automatically enrich and synchronize verified candidates directly into opportunities.json, opportunities.csv, and the monthly audit note.")
```
3. At the end of `main()`, after writing `pending_scan.json`:
```python
if args.sync:
    print("\n[SYNC] Synchronizing verified candidates into central database...")
    added = sync_opportunities.sync_database(verified_candidates, DB_PATH, CSV_PATH, profile)
    audit_note = os.path.join(BASE_DIR, f"opportunities-audit-{datetime.now().strftime('%Y-%m')}.md")
    sync_opportunities.generate_monthly_audit(DB_PATH, audit_note, profile)
    print(f"[SUCCESS] Database synced (+{added} new records) and audit note updated: {audit_note}")
```

- [x] **Step 4: Run unit tests to verify they pass**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: PASS

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py tests/test_scan_opportunities.py
git commit -m "feat(opportunities): add native --sync flag to scan_opportunities.py"
```

---

### Task 4: Link Verification, Dead Requisition Archival, and Skill Invariant Hardening

**Files:**
- Modify: `004-work-opportunities/database/opportunities.json`
- Modify: `004-work-opportunities/database/archived_opportunities.json`
- Modify: `004-work-opportunities/database/opportunities.csv`
- Modify: `.agents/skills/opportunity-scout/SKILL.md`
- Modify: `004-work-opportunities/opportunities-audit-2026-10.md`

- [x] **Step 1: Archive expired Keysight Technologies opportunity**

Run `prune_opportunities.py` to archive the confirmed dead opportunity:
```powershell
python 004-work-opportunities/scripts/prune_opportunities.py --id opp-82-keysight-technologies-data-scientist-intern
```
Verify that `opportunities.json` now has 99 active live records and Keysight is recorded in `archived_opportunities.json`.

- [x] **Step 2: Harden link integrity rules in `SKILL.md`**

In `.agents/skills/opportunity-scout/SKILL.md`:
1. Update Step 3 & Step 4 to explicitly forbid synthesizing or guessing URLs. Mandate that all links in chat briefing tables MUST be copied verbatim from `apply_url` in `opportunities.json`.
2. Document the 5-Tier taxonomy:
   - Tier 1: Candidate Domestic / Home Market (Direct Legal Match)
   - Tier 2: Remote & Flexible Opportunities
   - Tier 3: Elite Target Hubs (Visa Sponsorship Track)
   - Tier 4: Canadian Co-op & International Hubs
   - Tier 5: General Domestic (Unverified Sponsorship)
3. Document the single turnkey command:
   ```powershell
   python 004-work-opportunities/scripts/scan_opportunities.py --audit-mode --sync
   ```

- [x] **Step 3: Update `opportunities-audit-2026-10.md`**

Regenerate or update `004-work-opportunities/opportunities-audit-2026-10.md` to display:
- The updated 5-tier distribution (Tier 1: 0, Tier 2: 31, Tier 3: 29, Tier 4: 22, Tier 5: 17).
- The 100% verified application links.

- [x] **Step 4: Run all unit tests to ensure clean green suite**

Run: `python -m unittest tests/test_scan_opportunities.py tests/test_sync_opportunities.py`
Expected: ALL PASS.

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/ .agents/skills/opportunity-scout/SKILL.md
git commit -m "docs & fix: archive dead keysight requisition, update SKILL.md rules and audit note"
```

---

## Plan Review Checklist
- [x] Spec coverage: Covers Tier 5 rename, turnkey native `--sync` pipeline, dead link archival, and briefing table link integrity.
- [x] No placeholders: Every step contains explicit code, commands, and expected results.
- [x] Type consistency: Matches existing classes (`CandidateProfile`, `CSV_FIELDS`, JSON schema).

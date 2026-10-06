# Fix Opportunity Scout Limit Parser, Premature Truncation, and Pipeline Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul candidate selection in `scan_opportunities.py` to prevent premature truncation, support streaming link verification until the target limit is reached, add role/domain filtering, balance feed diversity, and provide a dedicated audit mode for initial vault triages.

**Architecture:** Refactor `004-work-opportunities/scripts/scan_opportunities.py` to introduce `select_verified_candidates()` which verifies candidate links in batches until the user's requested limit of active opportunities is satisfied (backfilling past dead links). Add CLI arguments for `--role` (case-insensitive keyword matching), `--max-per-source` (feed diversity cap), and `--audit-mode` (cold-start baseline expansion with wider 90-day age window and higher default limit of 100 verified candidates). Update corresponding test suites in `tests/test_scan_opportunities.py` and documentation in `004-work-opportunities/scripts/README.md` and `.agents/skills/opportunity-scout/SKILL.md`.

**Tech Stack:** Python 3.8+, `argparse`, `unittest`, `concurrent.futures`, `json`, `re`.

---

## File Structure Map

- **Modify:**
  - `004-work-opportunities/scripts/scan_opportunities.py`:
    - Add `--role`, `--max-per-source`, and `--audit-mode` arguments to CLI parser.
    - Implement `select_verified_candidates(candidates, limit, verify_links=False, checker_func=None, max_per_source=None, batch_size=15)` to stream-verify links and backfill active slots.
    - Implement `filter_by_role(role_title, role_query)` helper.
    - Refactor `main()` to use the new selection pipeline.
  - `tests/test_scan_opportunities.py`:
    - Add unit tests for `--role` matching (single, comma-separated, case-insensitive).
    - Add unit tests for `select_verified_candidates` backfilling when top candidates are dead links.
    - Add unit tests for `max_per_source` diversity cap.
    - Add unit tests for `--audit-mode` default expansion.
  - `004-work-opportunities/scripts/README.md`:
    - Document new CLI parameters and usage examples.
  - `.agents/skills/opportunity-scout/SKILL.md`:
    - Update Step 1 and Step 2 instructions to reference `--role` and `--audit-mode`.

---

### Task 1: Implement Role and Domain Filtering (`--role`)

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py`
- Test: `tests/test_scan_opportunities.py`

- [x] **Step 1: Write the failing tests for role filtering**

Add test cases in `tests/test_scan_opportunities.py` testing the `matches_role_filter` helper and CLI `--role` integration:

```python
    def test_matches_role_filter_single_keyword(self):
        self.assertTrue(scan_opportunities.matches_role_filter("Data Scientist Intern", "data scientist"))
        self.assertTrue(scan_opportunities.matches_role_filter("Senior Machine Learning Engineer", "machine learning"))
        self.assertFalse(scan_opportunities.matches_role_filter("Frontend Software Engineer", "data scientist"))

    def test_matches_role_filter_comma_separated_keywords(self):
        query = "data scientist, machine learning, ai/ml"
        self.assertTrue(scan_opportunities.matches_role_filter("AI/ML Research Intern", query))
        self.assertTrue(scan_opportunities.matches_role_filter("Data Scientist - Analytics", query))
        self.assertFalse(scan_opportunities.matches_role_filter("Fullstack Developer", query))

    def test_matches_role_filter_empty_or_none(self):
        self.assertTrue(scan_opportunities.matches_role_filter("Any Role", None))
        self.assertTrue(scan_opportunities.matches_role_filter("Any Role", ""))
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: FAIL with `AttributeError: module 'scan_opportunities' has no attribute 'matches_role_filter'`

- [x] **Step 3: Implement `matches_role_filter` and integrate into `scan_opportunities.py`**

In `004-work-opportunities/scripts/scan_opportunities.py`:
1. Add `matches_role_filter(role_title: str, role_query: str | None) -> bool`:
```python
def matches_role_filter(role_title: str, role_query: str | None) -> bool:
    """
    Checks if a role title matches any keyword in a comma-separated query string.
    Case-insensitive. Returns True if role_query is None or empty.
    """
    if not role_query or not str(role_query).strip():
        return True
    title_lower = (role_title or "").lower()
    keywords = [k.strip().lower() for k in str(role_query).split(",") if k.strip()]
    if not keywords:
        return True
    return any(k in title_lower for k in keywords)
```
2. Add `--role` to `argparse` in `main()`:
```python
    parser.add_argument("--role", type=str, default=None, help="Filter job postings by role keyword (comma-separated, case-insensitive, e.g. 'data scientist, machine learning')")
```
3. Inside the `for p in postings:` loop in `main()`, skip non-matching roles:
```python
        for p in postings:
            if not matches_role_filter(p.get("role", ""), args.role):
                continue
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: PASS (All role filter tests passing).

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py tests/test_scan_opportunities.py
git commit -m "feat(scout): add role and domain keyword filtering to scanner"
```

---

### Task 2: Implement Stream Verification with Backfilling (`select_verified_candidates`)

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py`
- Test: `tests/test_scan_opportunities.py`

- [x] **Step 1: Write the failing tests for candidate stream verification and backfilling**

Add test cases in `tests/test_scan_opportunities.py` verifying that when top candidates have dead links, the selector continues checking subsequent candidates until `limit` verified candidates are collected:

```python
    def test_select_verified_candidates_backfills_dead_links(self):
        candidates = [
            {"company": f"Company {i}", "role": "SWE Intern", "apply_url": f"https://example.com/job/{i}"}
            for i in range(1, 11)
        ]
        # Simulate: jobs 1, 2, 3 are 404 dead links, jobs 4-10 are active
        def mock_checker(opp):
            job_num = int(opp["apply_url"].split("/")[-1])
            if job_num in [1, 2, 3]:
                return opp, False, "Dead Link (HTTP 404)"
            return opp, True, "Active (200 OK)"

        # We request limit=3 with verify_links=True
        # It should skip jobs 1-3, and return jobs 4, 5, 6
        selected = scan_opportunities.select_verified_candidates(
            candidates, limit=3, verify_links=True, checker_func=mock_checker, batch_size=2
        )
        self.assertEqual(len(selected), 3)
        self.assertEqual([c["company"] for c in selected], ["Company 4", "Company 5", "Company 6"])

    def test_select_verified_candidates_without_verification_slices_directly(self):
        candidates = [{"company": f"Company {i}", "role": "SWE"} for i in range(10)]
        selected = scan_opportunities.select_verified_candidates(candidates, limit=4, verify_links=False)
        self.assertEqual(len(selected), 4)
        self.assertEqual(selected[0]["company"], "Company 0")

    def test_select_verified_candidates_respects_all_flag(self):
        candidates = [{"company": f"Company {i}", "role": "SWE"} for i in range(10)]
        selected = scan_opportunities.select_verified_candidates(candidates, limit=None, verify_links=False)
        self.assertEqual(len(selected), 10)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: FAIL with `AttributeError: module 'scan_opportunities' has no attribute 'select_verified_candidates'`

- [x] **Step 3: Implement `select_verified_candidates` in `scan_opportunities.py`**

In `004-work-opportunities/scripts/scan_opportunities.py`:
1. Define `select_verified_candidates`:
```python
def select_verified_candidates(
    candidates: list,
    limit: int | None = 10,
    verify_links: bool = False,
    checker_func=None,
    max_per_source: int | None = None,
    batch_size: int = 15
) -> list:
    """
    Selects top viable candidates. When verify_links=True, batches candidates
    and probes live application URLs until `limit` verified active opportunities
    are collected (backfilling dead links) or candidates are exhausted.
    """
    if not candidates:
        return []

    target_limit = len(candidates) if limit is None else limit

    if not verify_links:
        return candidates[:target_limit]

    verified = []
    source_counts = {}

    for i in range(0, len(candidates), batch_size):
        chunk = candidates[i:i + batch_size]
        active_chunk = filter_candidate_links(chunk, checker_func=checker_func)
        for opp in active_chunk:
            src = opp.get("source_id", "unknown")
            if max_per_source is not None and source_counts.get(src, 0) >= max_per_source:
                continue
            source_counts[src] = source_counts.get(src, 0) + 1
            verified.append(opp)
            if len(verified) >= target_limit:
                return verified

    return verified
```
2. Refactor `main()` in `scan_opportunities.py` to replace lines 598–604 with `select_verified_candidates`:
```python
    target_limit = None if args.all else args.limit
    selected = select_verified_candidates(
        all_candidates,
        limit=target_limit,
        verify_links=args.verify_links,
        batch_size=15
    )
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: PASS (All stream verification and backfilling tests passing).

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py tests/test_scan_opportunities.py
git commit -m "fix(scout): stream verify candidate links with backfilling up to limit"
```

---

### Task 3: Feed Diversity Balancing (`--max-per-source`)

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py`
- Test: `tests/test_scan_opportunities.py`

- [x] **Step 1: Write the failing tests for source diversification**

Add test cases in `tests/test_scan_opportunities.py`:

```python
    def test_select_verified_candidates_source_diversity_cap(self):
        # 8 candidates from Source A, 4 candidates from Source B
        candidates = []
        for i in range(8):
            candidates.append({"company": f"A-Corp {i}", "role": "SWE", "source_id": "source-a"})
        for i in range(4):
            candidates.append({"company": f"B-Corp {i}", "role": "SWE", "source_id": "source-b"})

        # With max_per_source=2 and limit=4, Source A can take at most 2 slots
        selected = scan_opportunities.select_verified_candidates(
            candidates, limit=4, verify_links=False, max_per_source=2
        )
        self.assertEqual(len(selected), 4)
        a_count = sum(1 for c in selected if c["source_id"] == "source-a")
        b_count = sum(1 for c in selected if c["source_id"] == "source-b")
        self.assertEqual(a_count, 2)
        self.assertEqual(b_count, 2)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: FAIL if `max_per_source` without link verification is not applied in the non-verify branch.

- [x] **Step 3: Implement `max_per_source` in `select_verified_candidates` and CLI**

In `004-work-opportunities/scripts/scan_opportunities.py`:
1. Ensure `select_verified_candidates` enforces `max_per_source` in both `verify_links=False` and `verify_links=True` paths:
```python
    if not verify_links:
        if max_per_source is None:
            return candidates[:target_limit]
        selected = []
        source_counts = {}
        for opp in candidates:
            src = opp.get("source_id", "unknown")
            if source_counts.get(src, 0) < max_per_source:
                source_counts[src] = source_counts.get(src, 0) + 1
                selected.append(opp)
                if len(selected) >= target_limit:
                    break
        return selected
```
2. Add `--max-per-source` CLI argument to `main()`:
```python
    parser.add_argument("--max-per-source", type=int, default=None, help="Maximum candidates to admit from any single upstream feed")
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: PASS (Diversity tests passing).

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py tests/test_scan_opportunities.py
git commit -m "feat(scout): add source diversity balancing to prevent single-feed monopolization"
```

---

### Task 4: Add Audit Mode Flag (`--audit-mode`) for Cold-Start Triages

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py`
- Test: `tests/test_scan_opportunities.py`

- [x] **Step 1: Write the failing tests for `--audit-mode` CLI configuration**

Add test cases in `tests/test_scan_opportunities.py`:

```python
    def test_audit_mode_expands_defaults(self):
        parser = scan_opportunities.build_argument_parser()
        args = parser.parse_args(["--audit-mode"])
        self.assertTrue(args.audit_mode)
        # Verify resolved defaults in scan_opportunities: 90 days, 100 candidates, live link verification enabled
        resolved_days, resolved_limit, resolved_verify = scan_opportunities.resolve_runtime_parameters(args)
        self.assertEqual(resolved_days, 90)
        self.assertEqual(resolved_limit, 100)
        self.assertTrue(resolved_verify)

    def test_explicit_flags_override_audit_mode_defaults(self):
        parser = scan_opportunities.build_argument_parser()
        args = parser.parse_args(["--audit-mode", "--days", "14", "--limit", "25"])
        resolved_days, resolved_limit, resolved_verify = scan_opportunities.resolve_runtime_parameters(args)
        self.assertEqual(resolved_days, 14)
        self.assertEqual(resolved_limit, 25)
        self.assertTrue(resolved_verify)
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: FAIL with `AttributeError: module 'scan_opportunities' has no attribute 'build_argument_parser'`

- [x] **Step 3: Implement `build_argument_parser` and `resolve_runtime_parameters`**

In `004-work-opportunities/scripts/scan_opportunities.py`:
1. Extract argument parser creation into `build_argument_parser()`:
```python
def build_argument_parser():
    parser = argparse.ArgumentParser(description="Unified Opportunities Scanner with Dynamic Worldwide Location & Constraints Engine.")
    parser.add_argument("--days", type=int, default=None, help="Maximum age of job postings in days (default: 7, or 90 in audit mode)")
    parser.add_argument("--limit", type=int, default=None, help="Maximum candidates to export to pending_scan.json (default: 10, or 100 in audit mode)")
    parser.add_argument("--source", type=str, default=None, help="Filter to run only a specific source ID")
    parser.add_argument("--role", type=str, default=None, help="Filter job postings by role keyword (comma-separated, case-insensitive, e.g. 'data scientist, machine learning')")
    parser.add_argument("--max-per-source", type=int, default=None, help="Maximum candidates to admit from any single upstream feed")
    parser.add_argument("--all", action="store_true", help="Include all candidates without limiting batch size")
    parser.add_argument("--verify-links", action="store_true", help="Probe candidate apply_url to drop 404s and corporate ATS redirects before export.")
    parser.add_argument("--audit-mode", action="store_true", help="Comprehensive audit mode for initial triage (defaults to --days 90, --limit 100, --verify-links)")
    return parser

def resolve_runtime_parameters(args) -> tuple[int, int | None, bool]:
    is_audit = getattr(args, "audit_mode", False)
    default_days = 90 if is_audit else 7
    default_limit = 100 if is_audit else 10
    default_verify = True if is_audit else False

    days = args.days if args.days is not None else default_days
    limit = None if args.all else (args.limit if args.limit is not None else default_limit)
    verify = True if (args.verify_links or default_verify) else False
    return days, limit, verify
```
2. Call `build_argument_parser()` and `resolve_runtime_parameters(args)` in `main()`.

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: PASS (All audit mode tests passing).

- [x] **Step 5: Commit changes**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py tests/test_scan_opportunities.py
git commit -m "feat(scout): add audit-mode flag for comprehensive initial vault triage"
```

---

### Task 5: Update Script Documentation and Skill Guidelines

**Files:**
- Modify: `004-work-opportunities/scripts/README.md`
- Modify: `.agents/skills/opportunity-scout/SKILL.md`

- [x] **Step 1: Update `004-work-opportunities/scripts/README.md`**

Add documentation for `--role`, `--audit-mode`, `--max-per-source`, and streaming verification:
```markdown
### 4. Advanced CLI Flags
- `--role "data scientist, machine learning"`: Filter roles by case-insensitive keyword.
- `--audit-mode`: Comprehensive initial triage mode (`--days 90`, `--limit 100`, `--verify-links`).
- `--max-per-source 5`: Cap admissions per feed to guarantee diversity across sources.
- `--verify-links`: Live probe application URLs, backfilling dead links until the requested limit is filled.
```

- [x] **Step 2: Update `.agents/skills/opportunity-scout/SKILL.md`**

Update Step 1 in `.agents/skills/opportunity-scout/SKILL.md`:
```markdown
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
```

- [x] **Step 3: Run entire test suite to ensure clean integration**

Run: `python -m unittest tests/test_scan_opportunities.py`
Expected: PASS with 0 failures or errors.

- [x] **Step 4: Commit documentation updates**

```bash
git add 004-work-opportunities/scripts/README.md .agents/skills/opportunity-scout/SKILL.md
git commit -m "docs(scout): document role filtering, audit mode, and stream verification"
```

---

## Self-Review Checklist

1. **Spec Coverage**:
   - Premature truncation fixed? Yes (Task 2: `select_verified_candidates` stream-verifies and backfills).
   - Domain/role filtering added? Yes (Task 1: `--role` keyword matching).
   - Single-feed monopolization prevented? Yes (Task 3: `--max-per-source` diversity cap).
   - Cold-start / first audit handled? Yes (Task 4: `--audit-mode` expands days to 90, limit to 100, auto-verifies).
2. **Placeholder Scan**: No `TBD`, `TODO`, or vague instructions; all code blocks, commands, and expected outputs are fully specified.
3. **Type and Name Consistency**: `select_verified_candidates`, `matches_role_filter`, `build_argument_parser`, and `resolve_runtime_parameters` are consistent across Tasks 1–4.

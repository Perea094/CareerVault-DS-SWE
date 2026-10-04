# Stale Upstream Feeds & Corporate ATS Redirects Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate dead links and expired job recommendations in the Opportunity Scout by disabling stale upstream feeds, preventing yearless date parsing bugs, detecting corporate ATS HTTP 301/302 redirects to generic job catalogs, and adding live link verification.

**Architecture:**
1. In `sources.json`, permanently disable abandoned upstream repositories (such as `proyecto-nutria-mx`), and add header-based cycle staleness guards in `scan_opportunities.py` to prevent ingesting stale tables even if re-enabled.
2. In `adapters/base.py`, rewrite `parse_age_days()` to dynamically calculate day differences relative to `datetime.now()`, parse explicit 4-digit years, and support cycle/reference year anchoring so yearless dates from older cycles produce `age_days > 365` and get rejected.
3. In `prune_opportunities.py`, enhance `check_single_link()` to inspect `resp.geturl()`, detect corporate ATS redirects (Microsoft Careers, Amazon.jobs, Workday, Oracle, Greenhouse) that redirect away from specific requisitions to generic career search catalogs, expand soft-404 closed keyword signatures, and handle stdout UTF-8 encoding safely.
4. In `scan_opportunities.py`, add a `--verify-links` mode that uses concurrent link checking to weed out dead links and redirected catalogs before writing to `pending_scan.json`.

**Tech Stack:** Python 3.11+, `urllib.request`, `ssl`, `concurrent.futures`, `re`, `pytest`, `unittest`.

---

### Task 1: Disable Stale Feeds in `sources.json` & Add Feed Staleness Guards in `scan_opportunities.py`

**Files:**
- Modify: `004-work-opportunities/scripts/sources.json:99-106`
- Modify: `004-work-opportunities/scripts/scan_opportunities.py:410-435`
- Test: `tests/test_scan_opportunities.py`

- [ ] **Step 1: Write failing test in `tests/test_scan_opportunities.py` for stale feed detection and sources config**

Add test in `tests/test_scan_opportunities.py`:
```python
    def test_sources_json_proyecto_nutria_is_disabled(self):
        config_path = Path(__file__).resolve().parent.parent / "004-work-opportunities" / "scripts" / "sources.json"
        with open(config_path, "r", encoding="utf-8") as f:
            sources = json.load(f)
        nutria = next((s for s in sources if s["id"] == "proyecto-nutria-mx"), None)
        self.assertIsNotNone(nutria)
        self.assertFalse(nutria.get("enabled", True))
        self.assertIn("2024", nutria.get("note", ""))

    def test_detect_stale_upstream_feed_header(self):
        stale_content = """# Summer 2024 Tech Internships by Proyecto Nutria
This repository was created for the 2024 cycle and has been abandoned by its maintainers.

| Company | Role | Location | Date |
| Amazon | SDE Intern | Seattle | Oct 10 |
"""
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(stale_content, current_year=2026)
        self.assertTrue(is_stale)
        self.assertIn("2024", reason)

        active_content = """# Summer 2027 Tech Internships
Active community list for 2026 / 2027 internships.

| Company | Role | Location | Date |
| Figma | Data Science Intern | San Francisco | Oct 01 |
"""
        is_stale, reason = scan_opportunities.is_stale_upstream_feed(active_content, current_year=2026)
        self.assertFalse(is_stale)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_scan_opportunities.py -k "test_sources_json_proyecto_nutria or test_detect_stale_upstream_feed_header" -v`
Expected: FAIL (AttributeError: module has no attribute `is_stale_upstream_feed` and `enabled` is True).

- [ ] **Step 3: Update `sources.json` to disable `proyecto-nutria-mx`**

In `004-work-opportunities/scripts/sources.json`:
```json
  {
    "id": "proyecto-nutria-mx",
    "name": "Proyecto Nutria MX Tech Internships",
    "url": "https://raw.githubusercontent.com/Proyecto-Nutria/MX-Internships/master/README.md",
    "parser": "speedyapply",
    "category": "Mexico / Tech Internships",
    "enabled": false,
    "note": "Disabled: Upstream repository was created for the Summer 2024 cycle and has been abandoned by maintainers. Contains expired job requisitions."
  },
```

- [ ] **Step 4: Implement `is_stale_upstream_feed()` and guard in `scan_opportunities.py`**

In `004-work-opportunities/scripts/scan_opportunities.py`:
```python
def is_stale_upstream_feed(content: str, current_year: int = 2026) -> tuple[bool, str]:
    """
    Inspects feed markdown content and header to detect abandoned or expired cycles.
    Returns (is_stale, reason).
    """
    if not content:
        return False, ""
    
    first_lines = "\n".join(content.splitlines()[:15])
    
    # Check if the title explicitly mentions a prior year cycle and not current/future cycles
    past_cycle_match = re.search(r'\b(202[0-4])\b', first_lines)
    future_cycle_match = re.search(r'\b(202[5-9]|203[0-9])\b', first_lines)
    
    if past_cycle_match and not future_cycle_match:
        past_year = past_cycle_match.group(1)
        if int(past_year) < current_year:
            return True, f"Upstream feed header specifies expired {past_year} cycle without active 2026+ updates."
            
    if re.search(r'\b(abandoned|archived|deprecated|no longer maintained)\b', first_lines, re.IGNORECASE):
        if not future_cycle_match:
            return True, "Upstream feed is explicitly marked as abandoned or archived by maintainers."
            
    return False, ""
```

In `main()` inside feed processing loop:
```python
        try:
            content = fetch_content(src["url"])
            stale, reason = is_stale_upstream_feed(content)
            if stale:
                print(f"  [SKIP] Skipping stale source '{src['id']}': {reason}", file=sys.stderr)
                continue
            postings = p_func(content, src)
            print(f"  Parsed {len(postings)} total rows.")
        except Exception as e:
            print(f"  [FAIL] Failed fetching {src['name']}: {e}", file=sys.stderr)
            continue
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `py -3.11 -m pytest tests/test_scan_opportunities.py -k "test_sources_json_proyecto_nutria or test_detect_stale_upstream_feed_header" -v`
Expected: PASS.

---

### Task 2: Robust Date Parsing & Year Anchoring in `adapters/base.py`

**Files:**
- Modify: `004-work-opportunities/scripts/adapters/base.py:16-47`
- Create: `tests/test_adapters.py`

- [ ] **Step 1: Write failing tests in `tests/test_adapters.py` for date parsing and year anchoring**

Create `tests/test_adapters.py`:
```python
import unittest
from datetime import datetime
import os
import sys

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from adapters.base import parse_age_days

class TestAdaptersBase(unittest.TestCase):
    def test_parse_age_relative_strings(self):
        self.assertEqual(parse_age_days("today"), 0)
        self.assertEqual(parse_age_days("just now"), 0)
        self.assertEqual(parse_age_days("3d"), 3)
        self.assertEqual(parse_age_days("5 days"), 5)
        self.assertEqual(parse_age_days("2mo"), 60)
        self.assertEqual(parse_age_days("12h"), 0)

    def test_parse_age_explicit_past_year(self):
        ref_date = datetime(2026, 10, 4)
        # Oct 10, 2024 is ~724 days prior to Oct 4, 2026
        age = parse_age_days("Oct 10, 2024", reference_date=ref_date)
        self.assertGreater(age, 700)

        age_short = parse_age_days("10/24/2024", reference_date=ref_date)
        self.assertGreater(age_short, 700)

    def test_parse_age_yearless_date_current_year(self):
        ref_date = datetime(2026, 10, 4)
        # Oct 01 without year in 2026 cycle is 3 days old
        age = parse_age_days("Oct 01", reference_date=ref_date, default_year=2026)
        self.assertEqual(age, 3)

        # Sep 28 without year is 6 days old
        age_sep = parse_age_days("Sep 28", reference_date=ref_date, default_year=2026)
        self.assertEqual(age_sep, 6)

    def test_parse_age_yearless_date_past_default_year(self):
        ref_date = datetime(2026, 10, 4)
        # Yearless date in a table known to be 2024
        age = parse_age_days("Oct 10", reference_date=ref_date, default_year=2024)
        self.assertGreater(age, 700)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_adapters.py -v`
Expected: FAIL (parse_age_days doesn't take reference_date / default_year or handle 4-digit years).

- [ ] **Step 3: Implement dynamic date parser with explicit year support in `adapters/base.py`**

In `004-work-opportunities/scripts/adapters/base.py`:
```python
from datetime import datetime, date
import re

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12
}

def parse_age_days(age_str, reference_date=None, default_year=None):
    """
    Parses a variety of age/date strings into integer elapsed days.
    Supports relative strings ('today', '3d', '2mo'), slash dates ('10/24/2024'),
    and named month dates ('Oct 10', 'Oct 10, 2024').
    If dates are from a prior year, returns actual elapsed days (> 365).
    """
    if not age_str:
        return 999
    
    if reference_date is None:
        ref = datetime.now()
    elif isinstance(reference_date, datetime):
        ref = reference_date
    elif isinstance(reference_date, date):
        ref = datetime(reference_date.year, reference_date.month, reference_date.day)
    else:
        ref = datetime.now()

    target_year = default_year if default_year is not None else ref.year

    s = str(age_str).strip().lower()
    if any(k in s for k in ["today", "just now", "0d", "0 days"]):
        return 0

    m_d = re.search(r'^(\d+)\s*d', s)
    if m_d:
        return int(m_d.group(1))

    m_mo = re.search(r'^(\d+)\s*mo', s)
    if m_mo:
        return int(m_mo.group(1)) * 30

    m_hr = re.search(r'^(\d+)\s*h', s)
    if m_hr:
        return 0

    # Look for explicit 4-digit year in string
    year_match = re.search(r'\b(202[0-9])\b', s)
    parsed_year = int(year_match.group(1)) if year_match else target_year

    # Check for MM/DD/YYYY or MM/DD format
    slash_match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', s)
    if slash_match:
        m_num = int(slash_match.group(1))
        d_num = int(slash_match.group(2))
        if slash_match.group(3):
            y_val = int(slash_match.group(3))
            parsed_year = 2000 + y_val if y_val < 100 else y_val
        try:
            target_dt = datetime(parsed_year, m_num, d_num)
            delta = (ref - target_dt).days
            return max(0, delta)
        except ValueError:
            pass

    # Check for Month Name + Day format (e.g. "Oct 10", "Oct 10, 2024", "10 Oct")
    for mon_name, mon_num in MONTH_MAP.items():
        if mon_name in s:
            day_match = re.search(r'\b(\d{1,2})\b', s)
            if day_match:
                d_num = int(day_match.group(1))
                try:
                    target_dt = datetime(parsed_year, mon_num, d_num)
                    delta = (ref - target_dt).days
                    return max(0, delta)
                except ValueError:
                    return 30
            return 30

    return 7
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.11 -m pytest tests/test_adapters.py -v`
Expected: PASS.

---

### Task 3: Corporate ATS Redirect Sniffer & Soft-404 Detection in `prune_opportunities.py`

**Files:**
- Modify: `004-work-opportunities/scripts/prune_opportunities.py:1-110`
- Create: `tests/test_prune_opportunities.py`

- [ ] **Step 1: Write failing tests in `tests/test_prune_opportunities.py` for corporate ATS redirects and soft-404s**

Create `tests/test_prune_opportunities.py`:
```python
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import sys

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import prune_opportunities
from prune_opportunities import check_single_link, is_ats_redirected_to_catalog

class TestPruneOpportunities(unittest.TestCase):
    def test_detect_microsoft_careers_catalog_redirect(self):
        original_url = "https://jobs.careers.microsoft.com/global/en/job/1765432/Software-Engineer-Intern"
        redirected_url = "https://apply.careers.microsoft.com/careers"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Microsoft", reason)

    def test_detect_amazon_jobs_catalog_redirect(self):
        original_url = "https://amazon.jobs/en/jobs/2337339/software-development-engineer-intern"
        redirected_url = "https://amazon.jobs/en/search?base_query="
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Amazon", reason)

    def test_detect_workday_careers_redirect(self):
        original_url = "https://workday.wd5.myworkdayjobs.com/en-US/Workday/job/SWE-Intern_R-12345"
        redirected_url = "https://workday.wd5.myworkdayjobs.com/en-US/Workday/careers"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, redirected_url)
        self.assertTrue(is_redirected)
        self.assertIn("Workday", reason)

    def test_active_requisition_not_flagged_as_redirect(self):
        original_url = "https://job-boards.greenhouse.io/figma/jobs/6178857004?gh_jid=6178857004"
        final_url = "https://job-boards.greenhouse.io/figma/jobs/6178857004"
        is_redirected, reason = is_ats_redirected_to_catalog(original_url, final_url)
        self.assertFalse(is_redirected)

    def test_check_single_link_detects_soft_404_keywords(self):
        opp = {"company": "Acme", "role": "SWE", "apply_url": "https://example.com/job1"}
        mock_resp = MagicMock()
        mock_resp.geturl.return_value = "https://example.com/job1"
        mock_resp.read.return_value = b"<html><body>Search our other open roles. This job is no longer available.</body></html>"
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            _, is_active, reason = check_single_link(opp)
            self.assertFalse(is_active)
            self.assertIn("ATS Closed Message", reason)

    def test_check_single_link_detects_http_404(self):
        opp = {"company": "Acme", "role": "SWE", "apply_url": "https://example.com/job2"}
        import urllib.error
        http_err = urllib.error.HTTPError("https://example.com/job2", 404, "Not Found", {}, None)

        with patch("urllib.request.urlopen", side_effect=http_err):
            _, is_active, reason = check_single_link(opp)
            self.assertFalse(is_active)
            self.assertIn("HTTP 404", reason)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_prune_opportunities.py -v`
Expected: FAIL (NameError: `is_ats_redirected_to_catalog` not defined).

- [ ] **Step 3: Implement redirect sniffer and enhanced link checker in `prune_opportunities.py`**

In `004-work-opportunities/scripts/prune_opportunities.py`:
1. Reconfigure stdout/stderr at top of file:
```python
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
```
2. Expand `CLOSED_KEYWORDS`:
```python
CLOSED_KEYWORDS = [
    "no longer accepting applications",
    "this job is no longer available",
    "this posting has closed",
    "position has been filled",
    "requisition closed",
    "this job has been unlisted",
    "job not found",
    "the role you are looking for is no longer active",
    "job expired",
    "this vacancy has expired",
    "search our other open roles",
    "this requisition is closed",
    "the job you are trying to view is no longer available",
    "this position is no longer accepting applications",
    "this job listing has expired",
    "page you are looking for no longer exists",
    "we couldn't find that job",
    "sorry, this position has been filled",
    "sorry, this job is no longer open"
]
```
3. Implement `is_ats_redirected_to_catalog(original_url: str, final_url: str) -> tuple[bool, str]`:
```python
def is_ats_redirected_to_catalog(original_url: str, final_url: str) -> tuple[bool, str]:
    """
    Detects if an ATS request for a specific requisition ID was redirected (HTTP 301/302)
    to a generic company careers search catalog or homepage instead of the job post.
    """
    if not original_url or not final_url:
        return False, ""

    orig_clean = original_url.strip().rstrip("/")
    final_clean = final_url.strip().rstrip("/")
    if orig_clean == final_clean:
        return False, ""

    orig_lower = orig_clean.lower()
    final_lower = final_clean.lower()

    # Microsoft Careers Trap
    if "careers.microsoft.com" in orig_lower:
        if "apply.careers.microsoft.com/careers" in final_lower and "job/" not in final_lower:
            return True, "Redirected to Microsoft general careers search (Job Expired)"
        if final_clean.endswith("/careers") or final_clean.endswith("/careers/"):
            return True, "Redirected to Microsoft careers catalog (Job Expired)"

    # Amazon Jobs Trap
    if "amazon.jobs" in orig_lower:
        if "/jobs/" in orig_lower and ("/jobs/" not in final_lower or "amazon.jobs/en/search" in final_lower or final_clean.endswith("amazon.jobs/en")):
            return True, "Redirected away from Amazon job requisition to search portal (Job Closed)"

    # Workday Careers Trap
    if "myworkdayjobs.com" in orig_lower:
        if "/job/" in orig_lower and ("/job/" not in final_lower or final_clean.endswith("/careers") or final_clean.endswith("/search")):
            return True, "Redirected away from Workday requisition to careers catalog (Job Closed)"

    # Greenhouse Trap
    if "greenhouse.io" in orig_lower:
        if "/jobs/" in orig_lower and "/jobs/" not in final_lower:
            return True, "Redirected away from Greenhouse job board (Job Closed)"

    # Lever Trap
    if "lever.co" in orig_lower:
        # e.g. jobs.lever.co/company/req-id -> jobs.lever.co/company (lost requisition UUID)
        orig_parts = orig_clean.split("/")
        final_parts = final_clean.split("/")
        if len(orig_parts) > len(final_parts) and "lever.co" in final_lower:
            return True, "Redirected away from Lever job posting (Job Closed)"

    # Generic ATS Requisition Drop
    # If the original URL had an explicit requisition slug /job/123 or gh_jid=123, but final URL is generic root
    if re.search(r'/(?:job|jobs|requisition|posting)/[a-zA-Z0-9_\-]+', orig_lower):
        if re.search(r'/(?:careers|search|jobs|home|portal)$', final_lower.rstrip("/")):
            return True, "Redirected from specific requisition to generic portal (Job Closed)"

    return False, ""
```
4. Update `check_single_link(opp)`:
```python
def check_single_link(opp):
    url = opp.get("apply_url")
    if not url:
        return opp, False, "Missing URL"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            final_url = resp.geturl()

            # Check for corporate ATS redirects to generic search catalogs
            is_redirected, red_reason = is_ats_redirected_to_catalog(url, final_url)
            if is_redirected:
                return opp, False, red_reason

            # Read first 32KB of response content for soft-404 text signatures
            content = resp.read(32768).decode("utf-8", errors="ignore").lower()
            for kw in CLOSED_KEYWORDS:
                if kw in content:
                    return opp, False, f"ATS Closed Message: '{kw}'"

            return opp, True, "Active (200 OK)"
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            return opp, False, f"Dead Link (HTTP {e.code})"
        elif e.code in [401, 403]:
            # Often Cloudflare bot guard or gated ATS; assume active
            return opp, True, f"Protected ATS (HTTP {e.code})"
        return opp, False, f"HTTP Error {e.code}"
    except Exception as e:
        # Network timeout or DNS resolution failure
        return opp, True, f"Network timeout/skip: {e}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.11 -m pytest tests/test_prune_opportunities.py -v`
Expected: PASS.

---

### Task 4: Link Validation Integration in `scan_opportunities.py`

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py:440-488`
- Test: `tests/test_scan_opportunities.py`

- [ ] **Step 1: Write failing test in `tests/test_scan_opportunities.py` for `--verify-links` filter**

Add test in `tests/test_scan_opportunities.py`:
```python
    def test_filter_dead_links_with_verify_links(self):
        candidates = [
            {"company": "Active Corp", "role": "SWE Intern", "apply_url": "https://example.com/active"},
            {"company": "Dead Corp", "role": "Data Intern", "apply_url": "https://example.com/dead404"}
        ]
        def mock_checker(opp):
            if "dead404" in opp["apply_url"]:
                return opp, False, "Dead Link (HTTP 404)"
            return opp, True, "Active (200 OK)"

        verified = scan_opportunities.filter_candidate_links(candidates, checker_func=mock_checker)
        self.assertEqual(len(verified), 1)
        self.assertEqual(verified[0]["company"], "Active Corp")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_scan_opportunities.py -k test_filter_dead_links_with_verify_links -v`
Expected: FAIL (AttributeError: module has no attribute `filter_candidate_links`).

- [ ] **Step 3: Implement `filter_candidate_links()` and `--verify-links` argument in `scan_opportunities.py`**

In `004-work-opportunities/scripts/scan_opportunities.py`:
1. Import `check_single_link` from `prune_opportunities` (with fallback).
2. Implement `filter_candidate_links`:
```python
def filter_candidate_links(candidates: list, checker_func=None, max_workers: int = 8) -> list:
    """
    Probes application URLs of candidates using concurrent HTTP checks,
    weeding out dead links and generic ATS redirects.
    """
    if not candidates:
        return []
    if checker_func is None:
        try:
            from prune_opportunities import check_single_link
            checker_func = check_single_link
        except ImportError:
            return candidates

    verified = []
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(checker_func, candidates))

    for opp, is_active, reason in results:
        if is_active:
            verified.append(opp)
        else:
            print(f"  [DEAD LINK REMOVED] {opp.get('company')} - {opp.get('role')} ({reason})", file=sys.stderr)

    return verified
```
3. Add `--verify-links` argument to `argparse`:
```python
    parser.add_argument("--verify-links", action="store_true", help="Probe candidate apply_url to drop 404s and corporate ATS redirects before export.")
```
4. If `--verify-links` is set, filter selected candidates before saving to `pending_scan.json`:
```python
    if args.verify_links:
        print(f"\nVerifying live links for top {len(selected)} candidate roles...")
        selected = filter_candidate_links(selected)
        print(f"Retained {len(selected)} verified active opportunities.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `py -3.11 -m pytest tests/test_scan_opportunities.py -k test_filter_dead_links_with_verify_links -v`
Expected: PASS.

---

### Task 5: Database Audit Script Verification & Full Test Suite Pass

**Files:**
- Test: Full pytest suite (`py -3.11 -m pytest`)
- Run: `py -3.11 004-work-opportunities/scripts/prune_opportunities.py --check-links --dry-run`

- [ ] **Step 1: Run dry-run link verification across database**

Run: `py -3.11 004-work-opportunities/scripts/prune_opportunities.py --check-links --dry-run`
Verify it executes cleanly with UTF-8 support and reports status.

- [ ] **Step 2: Run the full test suite**

Run: `py -3.11 -m pytest`
Expected: All tests pass across the entire repository with 0 failures.

- [ ] **Step 3: Commit all changes**

Commit with message: `fix: eliminate stale feeds and corporate ATS redirects in opportunity scout`

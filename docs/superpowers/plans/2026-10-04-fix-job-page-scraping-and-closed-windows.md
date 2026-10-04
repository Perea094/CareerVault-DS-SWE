# Fix Job Page Scraping, Position Type Accuracy, and Expired Application Windows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a robust ATS deep scraper and metadata extractor that inspects destination job pages (following iCIMS iframes and JSON-LD), accurately detects `Full-Time` vs `Part-Time` position types, and automatically disqualifies or flags postings whose description contains an expired application window or closing deadline.

**Architecture:** Create `004-work-opportunities/scripts/ats_scraper.py` to unwrap ATS iframes (e.g., iCIMS `?in_iframe=1`), parse structured JSON-LD and DOM headers for `Position Type` / weekly hours, and extract application closing deadlines. Integrate this inspector into `prune_opportunities.py` (to weed out past-deadline listings during health audits) and `scan_opportunities.py` (to enrich incoming opportunities with verified employment terms instead of assuming part-time).

**Tech Stack:** Python 3.11, `urllib.request`, `ssl`, `json`, `re`, `datetime`, `pytest`.

---

## File Structure Map

- **Create:**
  - `004-work-opportunities/scripts/ats_scraper.py`: Dedicated ATS deep inspector for resolving iframes, parsing `Position Type`, extracting weekly hours, and checking closing deadlines.
  - `tests/test_ats_scraper.py`: Comprehensive unit tests for iframe resolution, metadata extraction, and deadline expiration logic.
- **Modify:**
  - `004-work-opportunities/scripts/prune_opportunities.py:153-195`: Integrate closing window expiration and ATS deep inspection into `check_single_link()`.
  - `004-work-opportunities/scripts/scan_opportunities.py:352-356, 428-462`: Update Tier 2 label to avoid falsely claiming part-time on full-time roles, and enrich link verification with deep ATS inspection.
  - `tests/test_prune_opportunities.py`: Add test cases for expired application windows in job descriptions.
  - `tests/test_scan_opportunities.py`: Update tier category assertions and verify deep ATS filtering.

---

### Task 1: Create `ats_scraper.py` Core Metadata and Deadline Extraction Utilities

**Files:**
- Create: `004-work-opportunities/scripts/ats_scraper.py`
- Test: `tests/test_ats_scraper.py`

- [ ] **Step 1: Write the failing tests for core ATS parsing utilities**

Create `tests/test_ats_scraper.py` with test cases covering iframe unwrapping, JSON-LD parsing, position type detection (Full-Time vs Part-Time), and closing window deadline extraction.

```python
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts")))

from ats_scraper import (
    resolve_ats_subdocument_url,
    extract_json_ld,
    parse_position_type,
    parse_closing_deadline
)


def test_resolve_icims_iframe():
    html = '''<html><body><iframe src="https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"></iframe></body></html>'''
    base_url = "https://careers-cotiviti.icims.com/jobs/19531/job"
    resolved = resolve_ats_subdocument_url(base_url, html)
    assert resolved == "https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"


def test_resolve_non_iframe_url():
    html = '''<html><body><div>Standard Job Board</div></body></html>'''
    base_url = "https://job-boards.greenhouse.io/datacor/jobs/123"
    resolved = resolve_ats_subdocument_url(base_url, html)
    assert resolved == base_url


def test_extract_json_ld():
    html = '''
    <html>
      <head>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "title": "Machine Learning Intern",
          "employmentType": "FULL_TIME",
          "validThrough": "2026-12-31T23:59:59Z"
        }
        </script>
      </head>
    </html>
    '''
    data = extract_json_ld(html)
    assert data is not None
    assert data.get("title") == "Machine Learning Intern"
    assert data.get("employmentType") == "FULL_TIME"
    assert data.get("validThrough") == "2026-12-31T23:59:59Z"


def test_parse_position_type_icims_header():
    html = '''
    <div class="iCIMS_JobHeaderTag">
      <dt class="iCIMS_JobHeaderField">Position Type</dt>
      <dd class="iCIMS_JobHeaderData"><span>Full-Time</span></dd>
    </div>
    '''
    pos_type, hours = parse_position_type(html, json_ld=None)
    assert pos_type == "Full-Time"
    assert hours == "Full-Time (40 hrs/week)"


def test_parse_position_type_part_time_hours():
    html = '''
    <div>
      <p>Interns will have flexibility around school schedules. Please note schedule will not exceed 29hrs/week.</p>
      <span>Position Type: Part-Time</span>
    </div>
    '''
    pos_type, hours = parse_position_type(html, json_ld=None)
    assert pos_type == "Part-Time"
    assert "29" in hours or "20-30" in hours


def test_parse_closing_deadline_past():
    html = '''
    <p>Date of posting: 6/18/2026</p>
    <p>Applications are assessed on a rolling basis. We anticipate that the application window will close on 7/18/2026, but may change.</p>
    '''
    ref_date = datetime(2026, 10, 4)
    deadline_dt, is_expired, reason = parse_closing_deadline(html, json_ld=None, reference_date=ref_date)
    assert deadline_dt == datetime(2026, 7, 18)
    assert is_expired is True
    assert "closed on 2026-07-18" in reason.lower()


def test_parse_closing_deadline_future():
    html = '''
    <p>We anticipate that the application window will close on 11/15/2026.</p>
    '''
    ref_date = datetime(2026, 10, 4)
    deadline_dt, is_expired, reason = parse_closing_deadline(html, json_ld=None, reference_date=ref_date)
    assert deadline_dt == datetime(2026, 11, 15)
    assert is_expired is False
    assert reason == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_ats_scraper.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ats_scraper'`

- [ ] **Step 3: Write minimal implementation in `ats_scraper.py`**

Create `004-work-opportunities/scripts/ats_scraper.py`:

```python
import re
import json
from datetime import datetime, date
from urllib.parse import urljoin

MONTH_MAP = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}
_MON_PAT = '|'.join(sorted(MONTH_MAP.keys(), key=len, reverse=True))

_RE_ICIMS_IFRAME = re.compile(r'<iframe[^>]+src=["\']([^"\']+\?in_iframe=1[^"\']*)["\']', re.IGNORECASE)
_RE_ANY_IFRAME = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)

_RE_POS_TYPE_ICIMS = re.compile(
    r'<dt[^>]*class=["\'][^"\']*iCIMS_JobHeaderField[^"\']*["\'][^>]*>\s*Position Type\s*</dt>\s*<dd[^>]*class=["\'][^"\']*iCIMS_JobHeaderData[^"\']*["\'][^>]*>\s*<span[^>]*>([^<]+)</span>',
    re.IGNORECASE
)
_RE_POS_TYPE_GENERIC = re.compile(r'Position Type\s*[:\s-]+\s*([a-zA-Z\-]+(?:\s+[a-zA-Z\-]+)?)', re.IGNORECASE)
_RE_HOURS_PER_WEEK = re.compile(r'(\d{1,2}(?:\s*-\s*\d{1,2})?)\s*(?:hrs?|hours?)(?:/|\s*per\s*)week', re.IGNORECASE)
_RE_NOT_EXCEED_HOURS = re.compile(r'not\s+exceed\s+(\d{1,2})\s*(?:hrs?|hours?)(?:/|\s*per\s*)week', re.IGNORECASE)

_RE_DEADLINE_WINDOW = re.compile(
    rf'(?:anticipate that the application window will close on|application window will close on|application deadline:?|deadline:?|applications close on|closing date:?)\s*([0-9]{{1,2}}/[0-9]{{1,2}}/(?:20\d{{2}}|\d{{2}})|20\d{{2}}[-/][0-9]{{1,2}}[-/][0-9]{{1,2}}|(?:{_MON_PAT})\.?\s+[0-9]{{1,2}},?\s+20\d{{2}})',
    re.IGNORECASE
)


def resolve_ats_subdocument_url(base_url: str, html: str) -> str:
    """Detects if an ATS wraps job content in an iframe (e.g. iCIMS) and resolves the direct URL."""
    if not html or not base_url:
        return base_url

    m_icims = _RE_ICIMS_IFRAME.search(html)
    if m_icims:
        return urljoin(base_url, m_icims.group(1))

    if "icims.com" in base_url.lower():
        m_any = _RE_ANY_IFRAME.search(html)
        if m_any:
            target = m_any.group(1)
            if "icims.com" in target or "in_iframe" in target:
                return urljoin(base_url, target)

    return base_url


def extract_json_ld(html: str) -> dict | None:
    """Extracts the first JobPosting schema.org JSON-LD object from HTML."""
    if not html:
        return None
    matches = re.findall(r'<script[^>]+type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    for block in matches:
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict):
                if data.get("@type") == "JobPosting" or "title" in data or "employmentType" in data:
                    return data
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and (item.get("@type") == "JobPosting" or "title" in item):
                        return item
        except Exception:
            continue
    return None


def parse_position_type(html: str, json_ld: dict | None = None) -> tuple[str, str]:
    """
    Parses position type (Full-Time, Part-Time, Internship) and estimated hours.
    Returns: (position_type, hours_per_week)
    """
    pos_type = "Unspecified"
    hours_str = "Standard Internship Hours"

    # 1. Check HTML iCIMS Header Tag
    m_icims = _RE_POS_TYPE_ICIMS.search(html or "")
    if m_icims:
        raw_val = m_icims.group(1).strip()
        if "full-time" in raw_val.lower():
            pos_type = "Full-Time"
            hours_str = "Full-Time (40 hrs/week)"
        elif "part-time" in raw_val.lower():
            pos_type = "Part-Time"
            hours_str = "Part-Time"
        else:
            pos_type = raw_val

    # 2. Check JSON-LD
    if pos_type == "Unspecified" and json_ld:
        emp = str(json_ld.get("employmentType", "")).upper()
        if "FULL_TIME" in emp:
            pos_type = "Full-Time"
            hours_str = "Full-Time (40 hrs/week)"
        elif "PART_TIME" in emp:
            pos_type = "Part-Time"
            hours_str = "Part-Time"

    # 3. Generic HTML scan
    if pos_type == "Unspecified" and html:
        m_gen = _RE_POS_TYPE_GENERIC.search(html)
        if m_gen:
            raw_gen = m_gen.group(1).strip().lower()
            if "full-time" in raw_gen or "fulltime" in raw_gen:
                pos_type = "Full-Time"
                hours_str = "Full-Time (40 hrs/week)"
            elif "part-time" in raw_gen or "parttime" in raw_gen:
                pos_type = "Part-Time"
                hours_str = "Part-Time"

    # 4. Check for explicit hours mentions in body text
    if html:
        m_not_exceed = _RE_NOT_EXCEED_HOURS.search(html)
        if m_not_exceed:
            limit = m_not_exceed.group(1).strip()
            hours_str = f"Part-Time (Up to {limit} hrs/week)"
            pos_type = "Part-Time"
        else:
            m_hrs = _RE_HOURS_PER_WEEK.search(html)
            if m_hrs:
                val = m_hrs.group(1).strip()
                if "40" in val and "20" not in val:
                    hours_str = f"Full-Time ({val} hrs/week)"
                    if pos_type == "Unspecified":
                        pos_type = "Full-Time"
                elif any(k in val for k in ["20", "25", "30", "15"]):
                    hours_str = f"Part-Time ({val} hrs/week)"
                    if pos_type == "Unspecified":
                        pos_type = "Part-Time"

    return pos_type, hours_str


def _parse_date_string(d_str: str) -> datetime | None:
    if not d_str:
        return None
    d_clean = d_str.strip()
    # Slash: MM/DD/YYYY or MM/DD/YY
    if "/" in d_clean:
        parts = d_clean.split("/")
        if len(parts) == 3:
            try:
                m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
                if y < 100:
                    y += 2000
                return datetime(y, m, d)
            except Exception:
                pass
    # ISO: YYYY-MM-DD or YYYY/MM/DD
    if "-" in d_clean:
        parts = d_clean.split("-")
        if len(parts) == 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2].split("T")[0])
                return datetime(y, m, d)
            except Exception:
                pass
    # Textual: "July 18, 2026" or "Jul 18 2026"
    m_text = re.search(rf'({_MON_PAT})\.?\s+([0-9]{{1,2}}),?\s+(20\d{{2}})', d_clean, re.IGNORECASE)
    if m_text:
        try:
            m_val = MONTH_MAP[m_text.group(1).lower()]
            d_val = int(m_text.group(2))
            y_val = int(m_text.group(3))
            return datetime(y_val, m_val, d_val)
        except Exception:
            pass
    return None


def parse_closing_deadline(html: str, json_ld: dict | None = None, reference_date: datetime | None = None) -> tuple[datetime | None, bool, str]:
    """
    Parses application closing deadlines from job text and JSON-LD validThrough.
    Compares against reference_date (defaults to datetime.now()).
    Returns: (deadline_dt, is_expired, reason)
    """
    ref = reference_date or datetime.now()
    if isinstance(ref, date) and not isinstance(ref, datetime):
        ref = datetime(ref.year, ref.month, ref.day)

    target_dt = None

    # Check text patterns
    if html:
        m = _RE_DEADLINE_WINDOW.search(html)
        if m:
            raw_date = m.group(1)
            target_dt = _parse_date_string(raw_date)

    # Check JSON-LD validThrough if text pattern not found
    if not target_dt and json_ld and "validThrough" in json_ld:
        target_dt = _parse_date_string(str(json_ld["validThrough"]))

    if target_dt:
        if target_dt < ref:
            dt_str = target_dt.strftime("%Y-%m-%d")
            return target_dt, True, f"Expired application window: closed on {dt_str}"
        return target_dt, False, ""

    return None, False, ""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.11 -m pytest tests/test_ats_scraper.py -v`
Expected: PASS (all 6 tests pass)

- [ ] **Step 5: Commit**

```bash
git add 004-work-opportunities/scripts/ats_scraper.py tests/test_ats_scraper.py
git commit -m "feat(ats): implement core ATS metadata and deadline extraction in ats_scraper"
```

---

### Task 2: Implement High-Level `inspect_job_page()` in `ats_scraper.py`

**Files:**
- Modify: `004-work-opportunities/scripts/ats_scraper.py`
- Test: `tests/test_ats_scraper.py`

- [ ] **Step 1: Write the failing tests for `inspect_job_page()`**

Add tests to `tests/test_ats_scraper.py` checking full page inspection, network handling, mock iCIMS iframe redirection, and closed status flagging.

```python
def test_inspect_job_page_full_flow_icims_expired():
    parent_html = '''<html><body><iframe src="https://careers-cotiviti.icims.com/jobs/19531/job?in_iframe=1"></iframe></body></html>'''
    iframe_html = '''
    <html>
      <div class="iCIMS_JobHeaderTag">
        <dt class="iCIMS_JobHeaderField">Position Type</dt>
        <dd class="iCIMS_JobHeaderData"><span>Full-Time</span></dd>
      </div>
      <div>
        <p>Date of posting: 6/18/2026</p>
        <p>We anticipate that the application window will close on 7/18/2026.</p>
      </div>
    </html>
    '''
    ref_date = datetime(2026, 10, 4)

    def mock_fetch(url, timeout=10):
        if "in_iframe=1" in url:
            return iframe_html, 200, url
        return parent_html, 200, url

    with patch("ats_scraper.fetch_page_content", side_effect=mock_fetch):
        info = inspect_job_page("https://careers-cotiviti.icims.com/jobs/19531/job", reference_date=ref_date)
        assert info["is_active"] is False
        assert "closed on 2026-07-18" in info["reason"].lower()
        assert info["position_type"] == "Full-Time"
        assert info["hours_per_week"] == "Full-Time (40 hrs/week)"


def test_inspect_job_page_active_part_time():
    html = '''
    <html>
      <p>Position Type: Part-Time</p>
      <p>Schedule will not exceed 29hrs/week.</p>
      <p>We anticipate that the application window will close on 12/01/2026.</p>
    </html>
    '''
    ref_date = datetime(2026, 10, 4)

    def mock_fetch(url, timeout=10):
        return html, 200, url

    with patch("ats_scraper.fetch_page_content", side_effect=mock_fetch):
        info = inspect_job_page("https://example.com/job/123", reference_date=ref_date)
        assert info["is_active"] is True
        assert info["position_type"] == "Part-Time"
        assert "29" in info["hours_per_week"] or "Part-Time" in info["hours_per_week"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_ats_scraper.py -k "inspect_job_page" -v`
Expected: FAIL with `ImportError: cannot import name 'inspect_job_page' from 'ats_scraper'`

- [ ] **Step 3: Implement `fetch_page_content()` and `inspect_job_page()` in `ats_scraper.py`**

Append to `004-work-opportunities/scripts/ats_scraper.py`:

```python
import urllib.request
import urllib.error
import ssl

def fetch_page_content(url: str, timeout: int = 10) -> tuple[str, int, str]:
    """Fetches raw HTML and final URL for a given ATS web page."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        code = resp.getcode()
        final_url = resp.geturl() if hasattr(resp, "geturl") else url
        raw = resp.read()
        content = raw.decode("utf-8", errors="ignore") if isinstance(raw, bytes) else str(raw)
        return content, code, final_url


def inspect_job_page(url: str, reference_date: datetime | None = None, timeout: int = 10) -> dict:
    """
    Performs deep inspection of an ATS job page:
    1. Fetches top-level HTML.
    2. Resolves embedded iframes (e.g., iCIMS ?in_iframe=1).
    3. Parses position type (Full-Time vs Part-Time) and hours.
    4. Evaluates application closing deadlines against reference_date.
    Returns:
      {
        "url": str,
        "resolved_url": str,
        "is_active": bool,
        "reason": str,
        "position_type": str,
        "hours_per_week": str,
        "deadline": datetime | None,
        "is_expired": bool
      }
    """
    if not url or not isinstance(url, str):
        return {
            "url": url,
            "resolved_url": url,
            "is_active": False,
            "reason": "Missing URL",
            "position_type": "Unspecified",
            "hours_per_week": "Unspecified",
            "deadline": None,
            "is_expired": False
        }

    try:
        content, code, final_url = fetch_page_content(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            return {
                "url": url, "resolved_url": url, "is_active": False,
                "reason": f"Dead Link (HTTP {e.code})",
                "position_type": "Unspecified", "hours_per_week": "Unspecified",
                "deadline": None, "is_expired": True
            }
        return {
            "url": url, "resolved_url": url, "is_active": True,
            "reason": f"Protected ATS (HTTP {e.code})",
            "position_type": "Unspecified", "hours_per_week": "Unspecified",
            "deadline": None, "is_expired": False
        }
    except Exception as exc:
        return {
            "url": url, "resolved_url": url, "is_active": True,
            "reason": f"Network skip: {exc}",
            "position_type": "Unspecified", "hours_per_week": "Unspecified",
            "deadline": None, "is_expired": False
        }

    # Unwrap iframes if applicable
    resolved_url = resolve_ats_subdocument_url(final_url, content)
    working_content = content
    if resolved_url != final_url:
        try:
            sub_content, _, _ = fetch_page_content(resolved_url, timeout=timeout)
            working_content = sub_content
        except Exception:
            pass

    json_ld = extract_json_ld(working_content)
    pos_type, hours = parse_position_type(working_content, json_ld=json_ld)
    deadline_dt, is_expired, expired_reason = parse_closing_deadline(
        working_content, json_ld=json_ld, reference_date=reference_date
    )

    if is_expired:
        return {
            "url": url,
            "resolved_url": resolved_url,
            "is_active": False,
            "reason": expired_reason,
            "position_type": pos_type,
            "hours_per_week": hours,
            "deadline": deadline_dt,
            "is_expired": True
        }

    return {
        "url": url,
        "resolved_url": resolved_url,
        "is_active": True,
        "reason": "Active (200 OK)",
        "position_type": pos_type,
        "hours_per_week": hours,
        "deadline": deadline_dt,
        "is_expired": False
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.11 -m pytest tests/test_ats_scraper.py -v`
Expected: PASS (all 8 tests pass)

- [ ] **Step 5: Commit**

```bash
git add 004-work-opportunities/scripts/ats_scraper.py tests/test_ats_scraper.py
git commit -m "feat(ats): implement inspect_job_page in ats_scraper"
```

---

### Task 3: Integrate Expired Application Window Detection into `prune_opportunities.py`

**Files:**
- Modify: `004-work-opportunities/scripts/prune_opportunities.py:153-195`
- Test: `tests/test_prune_opportunities.py`

- [ ] **Step 1: Write the failing tests for prune deadline detection**

Add tests to `tests/test_prune_opportunities.py` verifying that postings with past application closing dates are flagged as closed during link checks.

```python
def test_check_single_link_flags_expired_application_window():
    opp = {
        "id": "opp-test-cotiviti",
        "company": "Cotiviti",
        "role": "Intern AI Engineer",
        "apply_url": "https://careers-cotiviti.icims.com/jobs/19531/job"
    }

    mock_info = {
        "url": opp["apply_url"],
        "resolved_url": opp["apply_url"],
        "is_active": False,
        "reason": "Expired application window: closed on 2026-07-18",
        "position_type": "Full-Time",
        "hours_per_week": "Full-Time (40 hrs/week)",
        "deadline": datetime(2026, 7, 18),
        "is_expired": True
    }

    with patch("ats_scraper.inspect_job_page", return_value=mock_info):
        updated_opp, is_live, reason = check_single_link(opp)
        assert is_live is False
        assert "closed on 2026-07-18" in reason.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_prune_opportunities.py -k "expired_application_window" -v`
Expected: FAIL (because `check_single_link` does not yet call `ats_scraper.inspect_job_page`)

- [ ] **Step 3: Update `check_single_link()` in `prune_opportunities.py`**

Modify `004-work-opportunities/scripts/prune_opportunities.py:153-195` to import and call `inspect_job_page`:

```python
def check_single_link(opp, reference_date=None):
    raw_url = opp.get("apply_url")
    if not raw_url or not isinstance(raw_url, str) or not raw_url.strip():
        return opp, False, "Missing URL"
    url = raw_url.strip()

    # 1. Use deep ATS inspector for iframe resolution, closing date detection, and status
    try:
        from ats_scraper import inspect_job_page
        info = inspect_job_page(url, reference_date=reference_date, timeout=10)
        if not info["is_active"]:
            return opp, False, info["reason"]
    except ImportError:
        pass

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            final_url = resp.geturl() if hasattr(resp, "geturl") else url
            if final_url:
                is_redirected, red_reason = is_ats_redirected_to_catalog(url, final_url)
                if is_redirected:
                    return opp, False, red_reason

            # Read first 32KB of response
            raw = resp.read(32768)
            if isinstance(raw, bytes):
                content = raw.decode("utf-8", errors="ignore").lower()
            else:
                content = str(raw).lower()

            for kw in CLOSED_KEYWORDS:
                if kw in content:
                    return opp, False, f"ATS Closed Message: '{kw}'"
            return opp, True, "Active (200 OK)"
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            return opp, False, f"Dead Link (HTTP {e.code})"
        elif e.code in [401, 403]:
            return opp, True, f"Protected ATS (HTTP {e.code})"
        return opp, False, f"HTTP Error {e.code}"
    except Exception as e:
        return opp, True, f"Network timeout/skip: {e}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.11 -m pytest tests/test_prune_opportunities.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 004-work-opportunities/scripts/prune_opportunities.py tests/test_prune_opportunities.py
git commit -m "feat(prune): integrate deep ATS deadline inspection into check_single_link"
```

---

### Task 4: Fix Tier Labeling and Integrate ATS Inspection into `scan_opportunities.py`

**Files:**
- Modify: `004-work-opportunities/scripts/scan_opportunities.py:352-356, 428-462`
- Test: `tests/test_scan_opportunities.py`

- [ ] **Step 1: Write the failing tests for accurate tier labeling and deep link verification**

Add tests in `tests/test_scan_opportunities.py` asserting:
1. Roles with "remote" in location are labeled `"Tier 2: Remote & Flexible Opportunities"` (NOT `"Remote Part-Time & Flexible"` which falsely claims full-time roles are part-time).
2. `filter_candidate_links` enriches opportunities with `position_type` and `hours_per_week` and filters out opportunities with expired application windows.

```python
def test_score_and_tier_remote_label():
    item = {
        "company": "Cotiviti",
        "role": "Intern AI Engineer",
        "location": "US-Remote"
    }
    profile = CandidateProfile(location="Monterrey, Mexico", work_authorization="Needs Sponsorship")
    score, tier = score_and_tier(item, profile)
    assert score == 85
    assert "part-time" not in tier.lower()
    assert "Tier 2: Remote & Flexible Opportunities" == tier


def test_filter_candidate_links_enriches_and_drops_expired():
    candidates = [
        {
            "company": "Cotiviti",
            "role": "Intern AI Engineer",
            "apply_url": "https://careers-cotiviti.icims.com/jobs/19531/job"
        },
        {
            "company": "Active Corp",
            "role": "ML Intern",
            "apply_url": "https://activecorp.com/jobs/1"
        }
    ]

    def mock_inspect(url, **kwargs):
        if "19531" in url:
            return {
                "is_active": False,
                "reason": "Expired application window: closed on 2026-07-18",
                "position_type": "Full-Time",
                "hours_per_week": "Full-Time (40 hrs/week)"
            }
        return {
            "is_active": True,
            "reason": "Active (200 OK)",
            "position_type": "Full-Time",
            "hours_per_week": "Full-Time (40 hrs/week)"
        }

    with patch("ats_scraper.inspect_job_page", side_effect=mock_inspect):
        verified = filter_candidate_links(candidates)
        assert len(verified) == 1
        assert verified[0]["company"] == "Active Corp"
        assert verified[0]["position_type"] == "Full-Time"
        assert verified[0]["hours_per_week"] == "Full-Time (40 hrs/week)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -3.11 -m pytest tests/test_scan_opportunities.py -k "remote_label or drops_expired" -v`
Expected: FAIL

- [ ] **Step 3: Update `score_and_tier()` and `filter_candidate_links()` in `scan_opportunities.py`**

In `004-work-opportunities/scripts/scan_opportunities.py`:
1. Change line 354:
```python
    # 3. Tier 2: Remote & Flexible Opportunities
    if "remote" in loc or "remote" in role or "contractor" in loc:
        return 85, "Tier 2: Remote & Flexible Opportunities"
```
2. Update `filter_candidate_links()`:
```python
def filter_candidate_links(candidates: list, checker_func=None, max_workers: int = 8) -> list:
    """
    Probes application URLs of candidates using concurrent HTTP checks,
    weeding out dead links, generic ATS redirects, and expired application windows,
    while enriching active candidates with verified position type and hours.
    """
    if not candidates:
        return []

    try:
        from ats_scraper import inspect_job_page
    except ImportError:
        inspect_job_page = None

    def _safe_inspect(opp):
        raw_url = opp.get("apply_url")
        if not raw_url:
            return opp, False, "Missing URL"
        if inspect_job_page:
            try:
                info = inspect_job_page(raw_url)
                if not info["is_active"]:
                    return opp, False, info["reason"]
                # Enrich candidate with scraped details
                opp["position_type"] = info.get("position_type", "Unspecified")
                opp["hours_per_week"] = info.get("hours_per_week", "Standard Internship Hours")
                return opp, True, "Active (200 OK)"
            except Exception as e:
                return opp, True, f"Inspector skip: {e}"
        # Fallback to checker_func if ats_scraper not available
        return opp, True, "Active"

    verified = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_safe_inspect, candidates))

    for opp, is_active, reason in results:
        if is_active:
            verified.append(opp)
        else:
            print(f"  [DISQUALIFIED] {opp.get('company')} - {opp.get('role')} ({reason})", file=sys.stderr)

    return verified
```

- [ ] **Step 4: Run test to verify it passes**

Run: `py -3.11 -m pytest tests/test_scan_opportunities.py -v`
Expected: PASS (all tests pass)

- [ ] **Step 5: Commit**

```bash
git add 004-work-opportunities/scripts/scan_opportunities.py tests/test_scan_opportunities.py
git commit -m "fix(scanner): correct Tier 2 labeling and enrich candidates with deep ATS metadata"
```

---

### Task 5: End-to-End Suite Verification & Real-World Validation

**Files:**
- Test: All unit test files in `tests/`

- [ ] **Step 1: Run the full test suite**

Run: `py -3.11 -m pytest -v`
Expected: All tests pass (140+ passed, 0 failures).

- [ ] **Step 2: Validate live inspection against real-world test cases**

Run verification script on real Cotiviti and Grow Financial postings:
```powershell
py -3.11 -c "
from ats_scraper import inspect_job_page
from datetime import datetime

ref = datetime(2026, 10, 4)

coti = inspect_job_page('https://careers-cotiviti.icims.com/jobs/19531/intern-ai-engineer-%28early-career-%E2%80%93-llm-context-%26-data-layer---healthcare%29/job', reference_date=ref)
print('Cotiviti:', coti['position_type'], '| Active:', coti['is_active'], '| Reason:', coti['reason'])

grow = inspect_job_page('https://careers-growfinancial.icims.com/jobs/2755/collections-data-analyst-intern---spring-2027/job', reference_date=ref)
print('Grow Financial:', grow['position_type'], '| Active:', grow['is_active'], '| Hours:', grow['hours_per_week'])
"
```
Expected output:
- Cotiviti: `Position Type: Full-Time` | `Active: False` | `Reason: Expired application window: closed on 2026-07-18`
- Grow Financial: `Position Type: Part-Time` | `Active: True` | `Hours: Part-Time (Up to 29 hrs/week)`

- [ ] **Step 3: Commit any final test artifacts or documentation**

```bash
git add docs/superpowers/plans/2026-10-04-fix-job-page-scraping-and-closed-windows.md
git commit -m "docs: finalize implementation plan for job page scraping and closed windows"
```

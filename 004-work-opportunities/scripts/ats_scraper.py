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
    rf'(?:anticipate that the application window will close on|application window will close on|application deadline:?|deadline:?|applications close on|closing date:?)\s*([0-9]{{1,2}}/[0-9]{{1,2}}/(?:20\d{{2}}|\d{{2}})|20\d{{2}}[-/][0-9]{{1,2}}[-/][0-9]{{1,2}}|(?:{_MON_PAT})\.?\s+[0-9]{{1,2}}(?:st|nd|rd|th)?,?\s+20\d{{2}})',
    re.IGNORECASE
)


def resolve_ats_subdocument_url(base_url: str, html: str) -> str:
    """Detects if an ATS wraps job content in an iframe (e.g. iCIMS) and resolves the direct URL."""
    if not html or not base_url:
        return base_url

    # Iterate through all iframe candidates so tracking/analytics iframes don't block resolution
    for m in _RE_ANY_IFRAME.finditer(html):
        src = m.group(1)
        if "in_iframe" in src.lower():
            return urljoin(base_url, src)

    if "icims.com" in base_url.lower():
        for m in _RE_ANY_IFRAME.finditer(html):
            src = m.group(1)
            if "icims.com" in src.lower():
                return urljoin(base_url, src)

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
                if isinstance(data.get("@graph"), list):
                    for item in data["@graph"]:
                        if isinstance(item, dict) and (item.get("@type") == "JobPosting" or "title" in item or "employmentType" in item):
                            return item
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and (item.get("@type") == "JobPosting" or "title" in item or "employmentType" in item):
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

    def _normalize(s: str) -> str:
        return s.replace("-", " ").replace("_", " ").lower()

    # 1. Check HTML iCIMS Header Tag
    m_icims = _RE_POS_TYPE_ICIMS.search(html or "")
    if m_icims:
        raw_val = m_icims.group(1).strip()
        norm_val = _normalize(raw_val)
        if "full time" in norm_val:
            pos_type = "Full-Time"
            hours_str = "Full-Time (40 hrs/week)"
        elif "part time" in norm_val:
            pos_type = "Part-Time"
            hours_str = "Part-Time"
        else:
            pos_type = raw_val

    # 2. Check JSON-LD
    if pos_type == "Unspecified" and json_ld:
        emp_raw = json_ld.get("employmentType", "")
        if isinstance(emp_raw, list):
            emp_raw = " ".join(str(x) for x in emp_raw)
        emp = _normalize(str(emp_raw))
        if "full time" in emp:
            pos_type = "Full-Time"
            hours_str = "Full-Time (40 hrs/week)"
        elif "part time" in emp:
            pos_type = "Part-Time"
            hours_str = "Part-Time"

    # 3. Generic HTML scan
    if pos_type == "Unspecified" and html:
        m_gen = _RE_POS_TYPE_GENERIC.search(html)
        if m_gen:
            raw_gen = _normalize(m_gen.group(1).strip())
            if "full time" in raw_gen:
                pos_type = "Full-Time"
                hours_str = "Full-Time (40 hrs/week)"
            elif "part time" in raw_gen:
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

    # ISO format (handles Z, offsets like -05:00, or YYYY-MM-DD)
    try:
        iso_clean = d_clean.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_clean)
        return dt.replace(tzinfo=None)
    except Exception:
        pass

    # Slash: MM/DD/YYYY, MM/DD/YY, or YYYY/MM/DD
    if "/" in d_clean:
        parts = d_clean.split("/")
        if len(parts) == 3:
            try:
                if len(parts[0]) == 4 or int(parts[0]) > 1000:
                    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
                    if y < 100:
                        y += 2000
                return datetime(y, m, d)
            except Exception:
                pass

    # Dash: YYYY-MM-DD or YYYY-M-D (fallback isolating date part from T, space, or offset)
    if "-" in d_clean:
        date_part = d_clean.split("T")[0].split(" ")[0]
        parts = date_part.split("-")
        if len(parts) == 3:
            try:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                return datetime(y, m, d)
            except Exception:
                pass

    # Textual: "July 18, 2026", "July 18th, 2026", "Jul 18 2026"
    m_text = re.search(rf'({_MON_PAT})\.?\s+([0-9]{{1,2}})(?:st|nd|rd|th)?,?\s+(20\d{{2}})', d_clean, re.IGNORECASE)
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

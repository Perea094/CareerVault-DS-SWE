import re
from datetime import datetime, date

# Precompiled regexes for text cleaning
_RE_HTML = re.compile(r'<[^>]+>')
_RE_MD_LINK = re.compile(r'\[([^\]]+)\]\([^\)]+\)')
_RE_SPACES = re.compile(r'\s+')

def clean_text(s):
    if not s:
        return ""
    # Strip HTML tags
    s = _RE_HTML.sub(' ', s)
    # Strip Markdown links [text](url) -> text
    s = _RE_MD_LINK.sub(r'\1', s)
    # Strip markdown bold/italics
    s = s.replace('**', '').replace('__', '')
    # Normalize whitespaces
    s = _RE_SPACES.sub(' ', s)
    return s.strip()

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

# Precompiled regexes for age and date parsing
_RE_HOURS = re.compile(r'\b(\d+)\s*(?:hours?|hrs?|h)\b')
_RE_DAYS = re.compile(r'\b(\d+)\s*(?:days?|d)\b')
_RE_WEEKS = re.compile(r'\b(\d+)\s*(?:weeks?|w)\b')
_RE_MONTHS = re.compile(r'\b(\d+)\s*(?:months?|mos?|mo)\b')
_RE_YEARS = re.compile(r'\b(\d+)\s*(?:years?|yrs?|y)\b')

_RE_YEAR_4DIGIT = re.compile(r'\b(20[0-9]{2})\b')
_RE_ISO = re.compile(r'\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})(?=[^\d]|$)')
_RE_SLASH = re.compile(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{4}|\d{2}))?(?=[^\d/]|$)')
_RE_MON_DAY = re.compile(rf'\b({_MON_PAT})\.?\s*[-/,]?\s*(\d{{1,2}})(?:st|nd|rd|th)?\b')
_RE_DAY_MON = re.compile(rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s*[-/,]?\s*({_MON_PAT})\b')
_RE_MON_YEAR = re.compile(rf'\b({_MON_PAT})\.?\s*[-/,]?\s*(20\d{{2}})\b')
_RE_YEAR_MON = re.compile(rf'\b(20\d{{2}})\s*[-/,]?\s*({_MON_PAT})\b')

def parse_age_days(age_str, reference_date=None, default_year=None) -> int:
    if not age_str:
        return 999

    s = clean_text(str(age_str)).lower()
    if not s:
        return 999

    # Determine reference date
    if reference_date is None:
        ref_dt = datetime.now()
    elif isinstance(reference_date, datetime):
        ref_dt = reference_date
    elif isinstance(reference_date, date):
        ref_dt = datetime(reference_date.year, reference_date.month, reference_date.day)
    else:
        ref_dt = datetime.now()

    ref = datetime(ref_dt.year, ref_dt.month, ref_dt.day)

    try:
        default_year = int(default_year) if default_year is not None else ref.year
    except (ValueError, TypeError):
        default_year = ref.year

    # Relative time strings
    if any(k in s for k in ["today", "just now"]):
        return 0
    if "yesterday" in s:
        return 1

    m_h = _RE_HOURS.search(s)
    if m_h:
        return 0

    m_d = _RE_DAYS.search(s)
    if m_d:
        return int(m_d.group(1))

    m_w = _RE_WEEKS.search(s)
    if m_w:
        return int(m_w.group(1)) * 7

    m_mo = _RE_MONTHS.search(s)
    if m_mo:
        return int(m_mo.group(1)) * 30

    m_y = _RE_YEARS.search(s)
    if m_y:
        return int(m_y.group(1)) * 365

    # Year detection: explicit 4-digit year or default_year
    year_match = _RE_YEAR_4DIGIT.search(s)
    if year_match:
        parsed_year = int(year_match.group(1))
    else:
        parsed_year = default_year

    # ISO format YYYY-MM-DD or YYYY/MM/DD
    m_iso = _RE_ISO.search(s)
    if m_iso:
        try:
            target_dt = datetime(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    # Slash dates: MM/DD/YYYY or MM/DD/YY or MM/DD
    m_slash = _RE_SLASH.search(s)
    if m_slash:
        try:
            m_month = int(m_slash.group(1))
            m_day = int(m_slash.group(2))
            yr_str = m_slash.group(3)
            if yr_str:
                yr = int(yr_str) if len(yr_str) == 4 else 2000 + int(yr_str)
            else:
                yr = parsed_year
            if m_month > 12 and 1 <= m_day <= 12:
                m_month, m_day = m_day, m_month
            target_dt = datetime(yr, m_month, m_day)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    # Month name dates with day: "Oct 10, 2024", "Oct 01", "Sep 28", "10 Oct", etc.
    m_mon_day = _RE_MON_DAY.search(s)
    if m_mon_day:
        try:
            m_month = MONTH_MAP[m_mon_day.group(1)]
            m_day = int(m_mon_day.group(2))
            target_dt = datetime(parsed_year, m_month, m_day)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    m_day_mon = _RE_DAY_MON.search(s)
    if m_day_mon:
        try:
            m_month = MONTH_MAP[m_day_mon.group(2)]
            m_day = int(m_day_mon.group(1))
            target_dt = datetime(parsed_year, m_month, m_day)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    # Month Year dates without day: "Oct 2024", "2024 Oct"
    m_mon_yr = _RE_MON_YEAR.search(s)
    if m_mon_yr:
        try:
            m_month = MONTH_MAP[m_mon_yr.group(1)]
            yr = int(m_mon_yr.group(2))
            target_dt = datetime(yr, m_month, 1)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    m_yr_mon = _RE_YEAR_MON.search(s)
    if m_yr_mon:
        try:
            m_month = MONTH_MAP[m_yr_mon.group(2)]
            yr = int(m_yr_mon.group(1))
            target_dt = datetime(yr, m_month, 1)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    return 7

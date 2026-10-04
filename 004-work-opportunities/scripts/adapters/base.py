import re

def clean_text(s):
    if not s:
        return ""
    # Strip HTML tags
    s = re.sub(r'<[^>]+>', ' ', s)
    # Strip Markdown links [text](url) -> text
    s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
    # Strip markdown bold/italics
    s = s.replace('**', '').replace('__', '')
    # Normalize whitespaces
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

from datetime import datetime, date

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

    if default_year is None:
        default_year = ref.year

    # Relative time strings
    if any(k in s for k in ["today", "just now", "0d", "0 days"]):
        return 0
    if "yesterday" in s:
        return 1

    m_h = re.search(r'\b(\d+)\s*(?:hours?|hrs?|h)\b', s)
    if m_h:
        return 0

    m_d = re.search(r'\b(\d+)\s*(?:days?|d)\b', s)
    if m_d:
        return int(m_d.group(1))

    m_mo = re.search(r'\b(\d+)\s*(?:months?|mos?|mo)\b', s)
    if m_mo:
        return int(m_mo.group(1)) * 30

    m_w = re.search(r'\b(\d+)\s*(?:weeks?|w)\b', s)
    if m_w:
        return int(m_w.group(1)) * 7

    # Year detection: explicit 4-digit year or default_year
    year_match = re.search(r'\b(20[0-9]{2})\b', s)
    if year_match:
        parsed_year = int(year_match.group(1))
    else:
        parsed_year = default_year

    # ISO format YYYY-MM-DD or YYYY/MM/DD
    m_iso = re.search(r'\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})(?=[^\d]|$)', s)
    if m_iso:
        try:
            target_dt = datetime(int(m_iso.group(1)), int(m_iso.group(2)), int(m_iso.group(3)))
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    # Slash dates: MM/DD/YYYY or MM/DD
    m_slash = re.search(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?(?=[^\d/]|$)', s)
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

    # Month name dates: "Oct 10, 2024", "Oct 01", "Sep 28", "10 Oct", etc.
    mon_pat = '|'.join(sorted(MONTH_MAP.keys(), key=len, reverse=True))

    m_mon_day = re.search(rf'\b({mon_pat})\.?\s*[-/,]?\s*(\d{{1,2}})(?:st|nd|rd|th)?\b', s)
    if m_mon_day:
        try:
            m_month = MONTH_MAP[m_mon_day.group(1)]
            m_day = int(m_mon_day.group(2))
            target_dt = datetime(parsed_year, m_month, m_day)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    m_day_mon = re.search(rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s*[-/,]?\s*({mon_pat})\b', s)
    if m_day_mon:
        try:
            m_month = MONTH_MAP[m_day_mon.group(2)]
            m_day = int(m_day_mon.group(1))
            target_dt = datetime(parsed_year, m_month, m_day)
            return max(0, (ref - target_dt).days)
        except (ValueError, OverflowError):
            pass

    return 7

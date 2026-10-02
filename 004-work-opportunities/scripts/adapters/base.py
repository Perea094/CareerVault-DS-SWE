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

def parse_age_days(age_str):
    if not age_str:
        return 999
    age_str = str(age_str).strip().lower()
    if any(k in age_str for k in ["today", "just now", "0d", "0 days"]):
        return 0
    m = re.search(r'(\d+)\s*d', age_str)
    if m:
        return int(m.group(1))
    m_mo = re.search(r'(\d+)\s*mo', age_str)
    if m_mo:
        return int(m_mo.group(1)) * 30
    m_hr = re.search(r'(\d+)\s*h', age_str)
    if m_hr:
        return 0
    # Month / Day format like "Oct 01" or "Sep 28"
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    for mon, num in months.items():
        if mon in age_str:
            m_day = re.search(r'(\d+)', age_str)
            if m_day:
                day = int(m_day.group(1))
                # October 2026 reference date
                if num == 10:
                    return max(0, 1 - day)
                elif num == 9:
                    return max(0, (30 - day) + 1)
                else:
                    return 30
    return 7

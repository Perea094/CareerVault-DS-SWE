import re
from .base import clean_text, parse_age_days

def parse_derec4(content, source_meta):
    """
    Parses DereC4/internships-and-newgrad README table:
    | Company | Role | Location | Age |
    """
    results = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith("|") or "---" in line or "Company" in line or "Role" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 4:
            continue

        comp_raw = cols[0]
        role_raw = cols[1]
        loc_raw = cols[2]
        age_raw = cols[3]

        url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', role_raw)
        if url_match:
            role = clean_text(url_match.group(1))
            apply_url = url_match.group(2).strip().rstrip("/")
        else:
            role = clean_text(role_raw)
            url_fallback = re.search(r'href=["\']([^"\']+)["\']', role_raw)
            apply_url = url_fallback.group(1).strip().rstrip("/") if url_fallback else None

        company = clean_text(comp_raw)
        location = clean_text(loc_raw)
        age = clean_text(age_raw)
        age_days = parse_age_days(age)

        if not company or not role or not apply_url:
            continue

        results.append({
            "source_id": source_meta.get("id", "derec4-tech-2027"),
            "source_name": source_meta.get("name", "DereC4 Tech Internships"),
            "company": company,
            "role": role,
            "location": location,
            "salary": "Not specified",
            "apply_url": apply_url,
            "age": age,
            "age_days": age_days,
            "sponsorship_notes": None
        })
    return results

def parse_negarprh(content, source_meta):
    """
    Parses negarprh/Canadian-Tech-Internships-2027 README table:
    | Company | Role | Location | Apply | Date Posted |
    """
    results = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith("|") or "---" in line or "Company" in line or "Role" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 5:
            continue

        comp_raw = cols[0]
        role_raw = cols[1]
        loc_raw = cols[2]
        app_raw = cols[3]
        date_raw = cols[4]

        # Extract target application link excluding shield badges
        urls = [u for u in re.findall(r'https?://[^\s\)\"\']+', app_raw) if "shields.io" not in u]
        apply_url = urls[0].strip().rstrip("/") if urls else None

        company = clean_text(comp_raw)
        role = clean_text(role_raw)
        loc = clean_text(loc_raw)
        # Ensure Canadian context is tagged if only city/province listed
        location = loc if ("canada" in loc.lower() or "remote" in loc.lower()) else f"{loc}, Canada"
        date_posted = clean_text(date_raw)
        age_days = parse_age_days(date_posted)

        if not company or not role or not apply_url:
            continue

        results.append({
            "source_id": source_meta.get("id", "negarprh-canada-2027"),
            "source_name": source_meta.get("name", "Canadian Tech Internships 2027"),
            "company": company,
            "role": role,
            "location": location,
            "salary": "Not specified",
            "apply_url": apply_url,
            "age": date_posted,
            "age_days": age_days,
            "sponsorship_notes": "Canada Opportunity (Co-op / Student Work Permit)"
        })
    return results

def parse_mehek(content, source_meta):
    """
    Parses mehek-builds/Summer2027-Internships lists:
    | Company | Role | Location | Pay | Application | Posted |
    """
    results = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith("|") or "---" in line or "Company" in line or "Role" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 6:
            continue

        comp_raw = cols[0]
        role_raw = cols[1]
        loc_raw = cols[2]
        pay_raw = cols[3]
        app_raw = cols[4]
        age_raw = cols[5]

        # Extract role clean text
        role_match = re.search(r'>([^<]+)</a>', role_raw)
        role = clean_text(role_match.group(1)) if role_match else clean_text(role_raw)

        # Direct ATS link preferred over intermediate trylitos links
        urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', app_raw)
        apply_url = None
        for u in urls:
            if "trylitos.com" not in u:
                apply_url = u.strip().rstrip("/")
                break
        if not apply_url and urls:
            apply_url = urls[0].strip().rstrip("/")

        company = clean_text(comp_raw)
        location = clean_text(loc_raw)
        salary = clean_text(pay_raw) or "Not specified"
        age = clean_text(age_raw)
        age_days = parse_age_days(age)

        if not company or not role or not apply_url:
            continue

        results.append({
            "source_id": source_meta.get("id", "mehek-summer-2027"),
            "source_name": source_meta.get("name", "Mehek Summer 2027 Internships"),
            "company": company,
            "role": role,
            "location": location,
            "salary": salary,
            "apply_url": apply_url,
            "age": age,
            "age_days": age_days,
            "sponsorship_notes": None
        })
    return results

def parse_lorenzo(content, source_meta):
    """
    Parses LorenzoLaCorte/european-tech-internships-2026 README table:
    | company | title | location | link |
    """
    results = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith("|") or "---" in line or "company" in line.lower() or "title" in line.lower():
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 4:
            continue

        company = clean_text(cols[0])
        role = clean_text(cols[1])
        location = clean_text(cols[2])
        link_col = cols[3]

        url_match = re.search(r'https?://[^\s\)\"\']+', link_col)
        apply_url = url_match.group(0).strip().rstrip("/") if url_match else None

        if not company or not role or not apply_url:
            continue

        results.append({
            "source_id": source_meta.get("id", "lorenzo-europe-2026"),
            "source_name": source_meta.get("name", "European Tech Opportunities"),
            "company": company,
            "role": role,
            "location": location,
            "salary": "Not specified",
            "apply_url": apply_url,
            "age": "Recent",
            "age_days": 14,
            "sponsorship_notes": "European Tech Opportunity"
        })
    return results

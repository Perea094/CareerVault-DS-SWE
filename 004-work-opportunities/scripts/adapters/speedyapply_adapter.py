import re
from .base import clean_text, parse_age_days

def parse_speedyapply(content, source_meta):
    results = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith("|") or "---" in line or "Position" in line or "Job Title" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 5:
            continue

        comp_raw = cols[0]
        pos_raw = cols[1]
        loc_raw = cols[2]

        if len(cols) >= 6:
            salary_raw = cols[3]
            post_raw = cols[4]
            age_raw = cols[5]
        else:
            salary_raw = "Not specified"
            post_raw = cols[3]
            age_raw = cols[4]

        # Extract apply URL
        url_match = re.search(r'href=["\']([^"\']+)["\']', post_raw)
        if not url_match:
            url_match = re.search(r'href=["\']([^"\']+)["\']', pos_raw)
        apply_url = url_match.group(1).strip().rstrip("/") if url_match else None

        company = clean_text(comp_raw)
        role = clean_text(pos_raw)
        location = clean_text(loc_raw)
        salary = clean_text(salary_raw)
        age = clean_text(age_raw)
        age_days = parse_age_days(age)

        if not company or not role:
            continue

        results.append({
            "source_id": source_meta.get("id", "speedyapply"),
            "source_name": source_meta.get("name", "SpeedyApply"),
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

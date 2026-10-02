import re
from .base import clean_text, parse_age_days

def parse_jobright(content, source_meta):
    results = []
    lines = content.splitlines()
    for line in lines:
        if not line.startswith("|") or "---" in line or "Job Title" in line or "Company" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) < 5:
            continue

        comp_col = cols[0]
        title_col = cols[1]
        loc_col = cols[2]
        model_col = cols[3]
        date_col = cols[4]

        # Extract company
        company = clean_text(comp_col)

        # Extract title and application link: [Job Title](url)
        url_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', title_col)
        if url_match:
            role = clean_text(url_match.group(1))
            apply_url = url_match.group(2).strip().rstrip("/")
        else:
            role = clean_text(title_col)
            url_fallback = re.search(r'href=["\']([^"\']+)["\']', title_col)
            apply_url = url_fallback.group(1).strip().rstrip("/") if url_fallback else None

        loc = clean_text(loc_col)
        work_model = clean_text(model_col)
        location = f"{loc} ({work_model})" if work_model else loc

        date_posted = clean_text(date_col)
        age_days = parse_age_days(date_posted)

        if not company or not role:
            continue

        results.append({
            "source_id": source_meta.get("id", "jobright"),
            "source_name": source_meta.get("name", "Jobright"),
            "company": company,
            "role": role,
            "location": location,
            "salary": "Not specified",
            "apply_url": apply_url,
            "age": date_posted,
            "age_days": age_days,
            "sponsorship_notes": None
        })
    return results

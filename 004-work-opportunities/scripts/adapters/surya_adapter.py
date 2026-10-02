import json
from datetime import datetime, timezone
from .base import clean_text, parse_age_days

def parse_surya(content, source_meta):
    results = []
    try:
        data = json.loads(content)
    except Exception:
        return results

    if not isinstance(data, list):
        return results

    now = datetime.now(timezone.utc)

    for item in data:
        if not item.get("active", True) or not item.get("is_visible", True):
            continue

        comp = clean_text(item.get("company_name", ""))
        role = clean_text(item.get("title", ""))
        locs = item.get("locations", [])
        loc = clean_text(", ".join(locs) if isinstance(locs, list) else str(locs or ""))
        url = (item.get("url") or "").strip().rstrip("/")

        if not comp or not role or not url:
            continue

        date_posted = item.get("date_posted")
        age_days = 7
        age_str = "Recent"
        if date_posted:
            try:
                dt = datetime.fromtimestamp(date_posted, tz=timezone.utc)
                age_days = max(0, (now - dt).days)
                age_str = f"{age_days}d"
            except Exception:
                pass

        spon = item.get("sponsorship")
        s_notes = f"Sponsorship: {spon}" if spon and spon != "Other" else None

        results.append({
            "source_id": source_meta.get("id", "surya-tracker"),
            "source_name": source_meta.get("name", "Surya Internship Tracker"),
            "company": comp,
            "role": role,
            "location": loc,
            "salary": "Not specified",
            "apply_url": url,
            "age": age_str,
            "age_days": age_days,
            "sponsorship_notes": s_notes
        })

    return results

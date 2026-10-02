import json
from datetime import datetime, timezone
from .base import clean_text, parse_age_days

def parse_zshah(content, source_meta):
    results = []
    try:
        data = json.loads(content)
    except Exception:
        return results

    if not isinstance(data, dict):
        return results

    now = datetime.now(timezone.utc)

    for job_id, job in data.items():
        if not job.get("is_open", False):
            continue

        comp = clean_text(job.get("company", ""))
        role = clean_text(job.get("title", ""))
        loc = clean_text(job.get("location", ""))
        url = (job.get("url") or "").strip().rstrip("/")
        if not comp or not role or not url:
            continue

        posted_at = job.get("posted_at")
        age_days = 7
        age_str = "Recent"
        if posted_at:
            try:
                dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                age_days = max(0, (now - dt).days)
                age_str = f"{age_days}d"
            except Exception:
                pass

        sponsorship = str(job.get("sponsorship", "")).lower()
        s_notes = None
        if sponsorship == "yes":
            s_notes = "Visa sponsorship available"
        elif sponsorship == "no":
            s_notes = "No visa sponsorship"

        results.append({
            "source_id": source_meta.get("id", "zshah101"),
            "source_name": source_meta.get("name", "zshah101 Auto-Internships"),
            "company": comp,
            "role": role,
            "location": loc,
            "salary": str(job.get("salary") or "Not specified"),
            "apply_url": url,
            "age": age_str,
            "age_days": age_days,
            "sponsorship_notes": s_notes
        })

    return results

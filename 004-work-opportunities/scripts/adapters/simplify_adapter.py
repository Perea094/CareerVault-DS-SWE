import re
from .base import clean_text, parse_age_days

def parse_simplify(content, source_meta):
    results = []
    # Split by table row
    tr_blocks = re.split(r'<tr[^>]*>', content, flags=re.IGNORECASE)
    
    last_company = ""

    for block in tr_blocks:
        if "<th" in block.lower():
            continue
        tds = re.findall(r'<td[^>]*>(.*?)</td>', block, flags=re.DOTALL | re.IGNORECASE)
        if len(tds) < 3:
            continue

        raw_comp = tds[0]
        raw_role = tds[1]
        raw_loc = tds[2] if len(tds) > 2 else ""
        raw_app = tds[3] if len(tds) > 3 else ""
        raw_age = tds[4] if len(tds) > 4 else (tds[-1] if len(tds) >= 4 else "0d")

        # Sponsorship and region flags from emojis
        sponsorship = []
        if "🛂" in block:
            sponsorship.append("US Citizenship Required")
        if "🔒" in block:
            sponsorship.append("No Visa Sponsorship")
        if "🇨🇦" in block:
            sponsorship.append("Canada Opportunity")
        if "🌐" in block:
            sponsorship.append("International Role")

        # Company parsing with inheritance
        clean_comp = clean_text(raw_comp)
        # Strip decorative icons like fire or arrow
        clean_comp = re.sub(r'[\U00010000-\U0010ffff]', '', clean_comp).strip()
        clean_comp = re.sub(r'^[↳\-\s\?]+', '', clean_comp).strip()

        if clean_comp and len(clean_comp) > 1 and not clean_comp.startswith("http"):
            company = clean_comp
            last_company = clean_comp
        else:
            company = last_company

        role = clean_text(raw_role)
        role = re.sub(r'[\U00010000-\U0010ffff]', '', role).strip()

        location = clean_text(raw_loc)
        age = clean_text(raw_age)
        age_days = parse_age_days(age)

        # Extract Apply URL (search in raw_app, then block)
        urls = re.findall(r'href=["\']([^"\']+)["\']', raw_app if raw_app else block)
        apply_url = None
        for u in urls:
            if "simplify.jobs/c/" in u:
                continue
            if u.startswith("http"):
                apply_url = u
                break

        if not company or not role:
            continue

        results.append({
            "source_id": source_meta.get("id", "simplify"),
            "source_name": source_meta.get("name", "SimplifyJobs"),
            "company": company,
            "role": role,
            "location": location,
            "salary": "Not specified",
            "apply_url": apply_url,
            "age": age,
            "age_days": age_days,
            "sponsorship_notes": "; ".join(sponsorship) if sponsorship else None
        })
    return results

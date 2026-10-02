import os
import sys
import json
import urllib.request
import argparse
import re

from adapters import get_parser

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "sources.json")
DB_PATH = os.path.join(BASE_DIR, "database", "opportunities.json")
ARCHIVE_PATH = os.path.join(BASE_DIR, "database", "archived_opportunities.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "database", "pending_scan.json")
PREFERENCES_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "001-background", "preferences.md"))

TOP_SPONSORS = [
    "figma", "adobe", "google", "meta", "jane street", "citadel", "susquehanna", "sig",
    "datarobot", "pathai", "amgen", "workiva", "ancestry", "hudson river trading", "hrt",
    "mistral", "nvidia", "microsoft", "salesforce", "pwc", "bbva", "shift technology",
    "waymo", "riot games", "pinterest", "glean", "amazon", "apple", "bloomberg"
]

def load_sources():
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] Sources configuration not found at {CONFIG_PATH}", file=sys.stderr)
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def load_existing():
    existing_urls = set()
    existing_titles = set()

    for path in [DB_PATH, ARCHIVE_PATH]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for opp in data.get("opportunities", []):
                        u = opp.get("apply_url")
                        if u:
                            existing_urls.add(u.strip().rstrip("/"))
                        c = opp.get("company", "").strip().lower()
                        r = opp.get("role", "").strip().lower()
                        if c and r:
                            existing_titles.add((c, r))
            except Exception as e:
                print(f"[WARN] Could not parse database {path}: {e}", file=sys.stderr)

    return existing_urls, existing_titles

def score_and_tier(item):
    """
    Score 0-100 and classify into Tier based on candidate constraints in preferences.md:
    - Querétaro, Mexico
    - No US visa (requires sponsorship, remote, or Mexican entity)
    - 20-30 hrs/week target during semester
    - Avoid Crypto
    """
    comp = item["company"].lower()
    role = item["role"].lower()
    loc = item["location"].lower()
    sponsorship = (item.get("sponsorship_notes") or "").lower()

    # 1. Hard Disqualifiers
    if "us citizenship required" in sponsorship:
        return -1, "Disqualified: US Citizenship Required"
    if any(k in comp or k in role for k in ["crypto", "web3", "blockchain", "solana", "ethereum"]):
        return -1, "Disqualified: Excluded Industry (Crypto/Web3)"
    if "phd" in role and not any(k in role for k in ["undergrad", "bachelor", "bs", "intern", "co-op"]):
        return -1, "Disqualified: Strict PhD Requirement"
    if "master" in role and not any(k in role for k in ["undergrad", "bachelor", "bs", "intern", "co-op"]):
        return -1, "Disqualified: Strict Master's Requirement"

    # 2. Tier 1: Mexico & LATAM
    mex_keywords = ["querétaro", "queretaro", "mexico city", "cdmx", "guadalajara", "monterrey", "apodaca", "jalisco", "zapopan"]
    is_mexico = any(m in loc for m in mex_keywords) or (bool(re.search(r'\bmexico\b', loc)) and "new mexico" not in loc)
    if is_mexico:
        return 95, "Tier 1: Mexico & LATAM (Direct Legal Match)"

    # 3. Tier 2: Remote / Part-Time
    if "remote" in loc or "remote" in role or "contractor" in loc:
        return 85, "Tier 2: Remote Part-Time & Flexible"

    # 4. Tier 4: Canadian Co-op
    can_keywords = ["canada", "toronto", "ontario", "ottawa", "vancouver", "montreal", "markham", "quebec"]
    if any(c in loc for c in can_keywords) or "canada" in sponsorship:
        return 75, "Tier 4: Canadian Co-op & International Hubs"

    # 5. Tier 3: Elite US Top Tech & Quant Sponsors
    if any(sp in comp for sp in TOP_SPONSORS):
        if "no visa sponsorship" in sponsorship:
            return 35, "Tier 3: US Sponsor (Sponsorship Warning)"
        return 65, "Tier 3: Elite US Summer 2027 (J-1 Visa Sponsor)"

    # 6. General US Roles
    if "no visa sponsorship" in sponsorship:
        return -1, "Disqualified: No Visa Sponsorship Available"

    if "us" in loc or "united states" in loc or "usa" in item.get("source_id", ""):
        return 45, "Tier 3: General US Opportunity"

    return 35, "Tier 4: International Opportunity"

def fetch_content(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def main():
    parser = argparse.ArgumentParser(description="Unified Opportunities Scanner for SpeedyApply, SimplifyJobs, and Jobright feeds.")
    parser.add_argument("--days", type=int, default=7, help="Maximum age of job postings in days (default: 7)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum candidates to export to pending_scan.json (default: 10)")
    parser.add_argument("--source", type=str, default=None, help="Filter to run only a specific source ID")
    parser.add_argument("--all", action="store_true", help="Include all candidates without limiting batch size")
    args = parser.parse_args()

    sources = load_sources()
    if args.source:
        sources = [s for s in sources if s["id"] == args.source]
        if not sources:
            print(f"[ERROR] Source '{args.source}' not found in configuration.", file=sys.stderr)
            return

    existing_urls, existing_titles = load_existing()
    print(f"Loaded database: {len(existing_titles)} registered opportunities ({len(existing_urls)} URLs).")

    all_candidates = []
    seen = set()

    for src in sources:
        if not src.get("enabled", True):
            continue

        p_func = get_parser(src.get("parser"))
        if not p_func:
            print(f"[WARN] Unknown parser '{src.get('parser')}' for source {src['id']}", file=sys.stderr)
            continue

        print(f"Fetching {src['name']} ({src['parser']})...")
        try:
            content = fetch_content(src["url"])
            postings = p_func(content, src)
            print(f"  Parsed {len(postings)} total rows.")
        except Exception as e:
            print(f"  [FAIL] Failed fetching {src['name']}: {e}", file=sys.stderr)
            continue

        for p in postings:
            # Check age
            if p["age_days"] > args.days:
                continue

            # Check deduplication
            u = p.get("apply_url")
            key = (p["company"].lower(), p["role"].lower())

            if u and u in existing_urls:
                continue
            if key in existing_titles or key in seen:
                continue

            # Require a valid application URL
            if not u:
                continue

            seen.add(key)
            seen.add(u)

            score, tier = score_and_tier(p)
            if score > 0:
                p["viability_score"] = score
                p["tier_category"] = tier
                all_candidates.append(p)

    # Sort candidates by viability score (descending), then age (ascending)
    all_candidates.sort(key=lambda x: (-x["viability_score"], x["age_days"]))

    limit = len(all_candidates) if args.all else args.limit
    selected = all_candidates[:limit]

    print(f"\n=======================================================")
    print(f"Scan Finished: Found {len(all_candidates)} viable new postings (Age <= {args.days}d).")
    print(f"Selected top {len(selected)} priority roles for audit.")
    print(f"=======================================================")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(selected, f, indent=2, ensure_ascii=False)

    print(f"Exported to: {OUTPUT_PATH}\n")

    def safe_str(v):
        return str(v or '').encode('ascii', errors='replace').decode('ascii')

    for idx, c in enumerate(selected, 1):
        print(f"{idx}. [{safe_str(c.get('tier_category'))}] {safe_str(c.get('company'))} - {safe_str(c.get('role'))}")
        print(f"   Location: {safe_str(c.get('location'))} | Age: {safe_str(c.get('age'))} | Source: {safe_str(c.get('source_name'))}")
        print(f"   Link: {c.get('apply_url')}")
        if c.get("sponsorship_notes"):
            print(f"   Notes: {safe_str(c.get('sponsorship_notes'))}")
        print()

if __name__ == "__main__":
    main()

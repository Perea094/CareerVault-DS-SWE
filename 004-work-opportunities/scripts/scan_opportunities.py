from __future__ import annotations

import os
import sys
import json
import urllib.request
import argparse
import re
from concurrent.futures import ThreadPoolExecutor

SCRIPTS_DIR = os.path.dirname(__file__)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    import ats_scraper
except ImportError:
    ats_scraper = None

try:
    from prune_opportunities import is_ats_redirected_to_catalog, check_single_link
except ImportError:
    is_ats_redirected_to_catalog = None
    check_single_link = None

from adapters import get_parser

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "sources.json")
DB_PATH = os.path.join(BASE_DIR, "database", "opportunities.json")
ARCHIVE_PATH = os.path.join(BASE_DIR, "database", "archived_opportunities.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "database", "pending_scan.json")
PREFERENCES_JSON_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "001-background", "preferences.json"))
PREFERENCES_MD_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "001-background", "preferences.md"))

TOP_SPONSORS = [
    "figma", "adobe", "google", "meta", "jane street", "citadel", "susquehanna", "sig",
    "datarobot", "pathai", "amgen", "workiva", "ancestry", "hudson river trading", "hrt",
    "mistral", "nvidia", "microsoft", "salesforce", "pwc", "bbva", "shift technology",
    "waymo", "riot games", "pinterest", "glean", "amazon", "apple", "bloomberg"
]

# Knowledge base of worldwide countries, aliases, negative patterns, and key tech hubs
COUNTRY_KB = {
    "mexico": {
        "aliases": ["mexico", "méxico", "mx"],
        "major_cities": [
            "querétaro", "queretaro", "mexico city", "cdmx", "guadalajara",
            "monterrey", "apodaca", "jalisco", "zapopan", "nuevo leon", "puebla"
        ],
        "negative_patterns": [r"\bnew mexico\b"],
        "display": "Mexico & Domestic Market",
    },
    "canada": {
        "aliases": ["canada", "ca"],
        "major_cities": [
            "toronto", "ontario", "ottawa", "vancouver", "montreal", "markham",
            "quebec", "waterloo", "calgary", "edmonton", "british columbia", "alberta"
        ],
        "negative_patterns": [],
        "display": "Canada & Domestic Market",
    },
    "united states": {
        "aliases": ["united states", "usa", "u.s.", "u.s.a.", "us", "america"],
        "major_cities": [
            "san francisco", "sf", "new york", "nyc", "seattle", "austin", "boston",
            "chicago", "los angeles", "california", "washington", "texas", "massachusetts"
        ],
        "negative_patterns": [],
        "display": "United States",
    },
    "united kingdom": {
        "aliases": ["united kingdom", "uk", "u.k.", "great britain", "england", "scotland", "wales", "britain"],
        "major_cities": ["london", "cambridge", "oxford", "manchester", "edinburgh", "bristol", "birmingham"],
        "negative_patterns": [],
        "display": "United Kingdom & Domestic Market",
    },
    "germany": {
        "aliases": ["germany", "deutschland", "de"],
        "major_cities": ["berlin", "munich", "münchen", "frankfurt", "hamburg", "stuttgart", "cologne", "köln"],
        "negative_patterns": [],
        "display": "Germany & Domestic Market",
    },
    "france": {
        "aliases": ["france", "fr"],
        "major_cities": ["paris", "lyon", "toulouse", "bordeaux", "grenoble", "marseille", "nantes"],
        "negative_patterns": [],
        "display": "France & Domestic Market",
    },
    "spain": {
        "aliases": ["spain", "españa", "es"],
        "major_cities": ["madrid", "barcelona", "valencia", "seville", "málaga", "bilbao"],
        "negative_patterns": [],
        "display": "Spain & Domestic Market",
    },
    "india": {
        "aliases": ["india", "in"],
        "major_cities": ["bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "chennai"],
        "negative_patterns": [r"\bindiana\b"],
        "display": "India & Domestic Market",
    },
    "brazil": {
        "aliases": ["brazil", "brasil", "br"],
        "major_cities": ["são paulo", "sao paulo", "rio de janeiro", "belo horizonte", "curitiba", "porto alegre"],
        "negative_patterns": [],
        "display": "Brazil & Domestic Market",
    },
    "australia": {
        "aliases": ["australia", "au"],
        "major_cities": ["sydney", "melbourne", "brisbane", "perth", "canberra", "adelaide"],
        "negative_patterns": [],
        "display": "Australia & Domestic Market",
    },
    "colombia": {
        "aliases": ["colombia", "co"],
        "major_cities": ["bogota", "bogotá", "medellin", "medellín", "cali", "barranquilla"],
        "negative_patterns": [r"\bcolumbia\b", r"\bbritish columbia\b", r"\bdistrict of columbia\b"],
        "display": "Colombia & Domestic Market",
    },
    "netherlands": {
        "aliases": ["netherlands", "holland", "nl"],
        "major_cities": ["amsterdam", "rotterdam", "utrecht", "eindhoven", "the hague"],
        "negative_patterns": [],
        "display": "Netherlands & Domestic Market",
    },
    "ireland": {
        "aliases": ["ireland", "ie"],
        "major_cities": ["dublin", "cork", "galway", "limerick"],
        "negative_patterns": [r"\bnorthern ireland\b"],
        "display": "Ireland & Domestic Market",
    },
    "switzerland": {
        "aliases": ["switzerland", "schweiz", "suisse", "ch"],
        "major_cities": ["zurich", "zürich", "geneva", "genève", "lausanne", "basel"],
        "negative_patterns": [],
        "display": "Switzerland & Domestic Market",
    },
    "singapore": {
        "aliases": ["singapore", "sg"],
        "major_cities": ["singapore"],
        "negative_patterns": [],
        "display": "Singapore & Domestic Market",
    }
}


class CandidateProfile:
    """
    Candidate Profile with dynamic worldwide location matching,
    work authorization resolution, and domain preference constraints.
    """
    def __init__(self, name="Candidate", location="City, Country", work_authorization="None",
                 disallowed_industries=None, target_hours="20-30"):
        self.name = name
        self.raw_location = location or "City, Country"
        self.work_authorization = work_authorization or "None"
        self.disallowed_industries = disallowed_industries or ["crypto", "web3", "blockchain", "solana", "ethereum"]
        self.target_hours = target_hours

        self.is_us_authorized = self._check_us_authorized()
        self.is_placeholder_location = self._check_placeholder_location()
        self.home_country_key, self.home_display, self.home_keywords, self.negative_patterns = self._resolve_location_rules()

    def _check_us_authorized(self):
        auth = self.work_authorization.lower()
        if any(k in auth for k in ["citizen", "permanent resident", "green card", "authorized", "us national"]):
            return True
        loc = self.raw_location.lower()
        if ("united states" in loc or re.search(r'\b(usa|us)\b', loc)) and not any(
            k in auth for k in ["none", "needs sponsorship", "unauthorized", "f-1", "j-1", "opt", "require"]
        ):
            return True
        return False

    def _check_placeholder_location(self):
        loc = self.raw_location.strip().lower()
        return not loc or loc in ["city, country", "city", "country", "placeholder", "tbd", "unknown"]

    def _resolve_location_rules(self):
        if self.is_placeholder_location:
            return None, "Domestic Market", [], []

        loc_lower = self.raw_location.lower()
        parts = [p.strip() for p in re.split(r'[,/|-]', loc_lower) if p.strip()]
        country_part = parts[-1] if parts else loc_lower
        region_parts = parts[:-1] if len(parts) > 1 else []

        # Match against knowledge base
        matched_kb = None
        matched_key = None
        for key, info in COUNTRY_KB.items():
            if any(alias == country_part or alias in parts or (len(alias) > 3 and alias in loc_lower) for alias in info["aliases"]):
                matched_kb = info
                matched_key = key
                break

        if matched_kb:
            keywords = list(matched_kb["major_cities"]) + list(matched_kb["aliases"])
            for r in region_parts:
                if len(r) > 2 and r not in keywords:
                    keywords.append(r)
            return matched_key, matched_kb["display"], keywords, matched_kb["negative_patterns"]

        # Universal fallback for any country/region globally
        clean_country = country_part.title()
        display = f"{clean_country} & Domestic Market"
        keywords = [country_part] + [r for r in region_parts if len(r) > 2]
        return country_part, display, keywords, []

    def is_domestic_match(self, job_location):
        if self.is_placeholder_location:
            return False

        loc_lower = (job_location or "").lower()
        if not loc_lower:
            return False

        # If candidate is US authorized and role is in the US
        if self.is_us_authorized:
            if any(k in loc_lower for k in ["united states", "usa"]) or re.search(r'\b(us|u\.s\.)\b', loc_lower):
                return True
            us_cities = COUNTRY_KB.get("united states", {}).get("major_cities", [])
            if any(k in loc_lower for k in us_cities):
                return True

        # Mask out negative patterns (e.g., 'new mexico' should not match country 'mexico')
        cleaned_loc = loc_lower
        for neg in self.negative_patterns:
            cleaned_loc = re.sub(neg, " ", cleaned_loc)

        # Check candidate city/state/country keywords against cleaned location
        for kw in self.home_keywords:
            if len(kw) <= 3:
                pattern = rf'\b{re.escape(kw)}\b'
                if re.search(pattern, cleaned_loc):
                    return True
            else:
                if kw in cleaned_loc:
                    return True

        return False


def load_candidate_profile(json_path=PREFERENCES_JSON_PATH, md_path=PREFERENCES_MD_PATH):
    name = "Candidate"
    loc = "City, Country"
    auth = "None"
    industries = ["crypto", "web3", "blockchain", "solana", "ethereum"]
    hours = "20-30"

    # 1. Load preferences.json
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cand = data.get("candidate", {})
            loc_visa = data.get("location_visa", {})
            ind_domain = data.get("industry_domain", {})
            career = data.get("career_goals", {})

            name = cand.get("name") or name
            loc = loc_visa.get("current_location") or cand.get("location") or loc
            auth = loc_visa.get("us_work_authorization") or cand.get("work_authorization") or auth

            avoid = ind_domain.get("industries_to_avoid") or career.get("disallowed_industries")
            if isinstance(avoid, list) and avoid:
                for a in avoid:
                    a_lower = str(a).strip().lower()
                    if a_lower and a_lower not in industries:
                        industries.append(a_lower)
            return CandidateProfile(name=name, location=loc, work_authorization=auth,
                                    disallowed_industries=industries, target_hours=hours)
        except Exception as e:
            print(f"[WARN] Error reading preferences JSON ({json_path}): {e}", file=sys.stderr)

    # 2. Fallback to preferences.md YAML frontmatter
    if os.path.exists(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            m = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if m:
                fm = m.group(1)
                loc_m = re.search(r'current_location:\s*["\']?([^"\']+)["\']?', fm)
                if loc_m:
                    loc = loc_m.group(1).strip()
                auth_m = re.search(r'us_work_authorization:\s*["\']?([^"\']+)["\']?', fm)
                if auth_m:
                    auth = auth_m.group(1).strip()
        except Exception:
            pass

    return CandidateProfile(name=name, location=loc, work_authorization=auth,
                            disallowed_industries=industries, target_hours=hours)


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


def score_and_tier(item, profile: CandidateProfile = None):
    """
    Score 0-100 and classify into priority Tier dynamically based on candidate constraints:
    - Profile home location (current_location in preferences.json)
    - US work authorization (us_work_authorization in preferences.json)
    - Disallowed industries (industries_to_avoid in preferences.json)
    - Schedule and degree prerequisites
    """
    if profile is None:
        profile = load_candidate_profile()

    comp = item["company"].lower()
    role = item["role"].lower()
    loc = item["location"].lower()
    sponsorship = (item.get("sponsorship_notes") or "").lower()

    # 1. Hard Disqualifiers
    # Excluded Industries (Crypto, Web3, etc.)
    for ind in profile.disallowed_industries:
        if ind in comp or ind in role:
            return -1, f"Disqualified: Excluded Industry ({ind.title()})"

    # Citizenship / Authorization Disqualifiers
    if not profile.is_us_authorized:
        if "us citizenship required" in sponsorship:
            return -1, "Disqualified: US Citizenship Required"
        is_us_role = any(k in loc for k in ["united states", "usa"]) or re.search(r'\b(us|u\.s\.)\b', loc) or "usa" in item.get("source_id", "")
        if is_us_role and "no visa sponsorship" in sponsorship:
            return -1, "Disqualified: No Visa Sponsorship Available"

    # Degree Gates
    if "phd" in role and not any(k in role for k in ["undergrad", "bachelor", "bs", "intern", "co-op"]):
        return -1, "Disqualified: Strict PhD Requirement"
    if "master" in role and not any(k in role for k in ["undergrad", "bachelor", "bs", "intern", "co-op"]):
        return -1, "Disqualified: Strict Master's Requirement"

    # 2. Tier 1: Candidate Domestic / Home Market (Direct Legal Match & Maximum Viability)
    if profile.is_domestic_match(loc):
        tier_label = f"Tier 1: {profile.home_display} (Direct Legal Match)"
        return 95, tier_label

    # 3. Tier 2: Remote & Flexible Opportunities
    if "remote" in loc or "remote" in role or "contractor" in loc:
        return 85, "Tier 2: Remote & Flexible Opportunities"

    # 4. Tier 4: International Co-op (e.g. Canadian Co-op for non-Canadians)
    can_keywords = ["canada", "toronto", "ontario", "ottawa", "vancouver", "montreal", "markham", "quebec", "waterloo"]
    if profile.home_country_key != "canada" and (any(c in loc for c in can_keywords) or "canada" in sponsorship):
        return 75, "Tier 4: Canadian Co-op & International Hubs"

    # 5. Tier 3: Elite US / Global Sponsoring Tech & Quant
    if any(sp in comp for sp in TOP_SPONSORS):
        if not profile.is_us_authorized and "no visa sponsorship" in sponsorship:
            return 35, "Tier 3: US Sponsor (Sponsorship Warning)"
        return 65, "Tier 3: Elite Target Hubs (Visa Sponsorship Track)"

    # 6. General US Roles
    if any(k in loc for k in ["united states", "usa"]) or re.search(r'\b(us|u\.s\.)\b', loc) or "usa" in item.get("source_id", ""):
        if profile.is_us_authorized:
            return 90, "Tier 1: United States (Direct Legal Match)"
        return 45, "Tier 3: General US Opportunity"

    # 7. General International Roles
    return 35, "Tier 4: International Opportunity"


def fetch_content(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def is_stale_upstream_feed(content: str, current_year: int = 2026) -> tuple[bool, str]:
    """
    Detect whether an upstream feed or repository README is stale, abandoned,
    or belongs to an expired recruiting cycle.

    Parameters:
        content (str): The raw text or markdown content of the feed.
        current_year (int): The current active recruiting cycle year (default: 2026).
            Years >= current_year are considered active cycles.
            Years < current_year (and >= 2000) are considered prior/expired cycles.

    Returns:
        tuple[bool, str]: A tuple of (is_stale, reason).
            - (False, "") if the feed is active or is a structured JSON feed.
            - (True, reason) if the feed header specifies an expired cycle without
              active updates, or is explicitly marked as abandoned/archived.
    """
    if not content:
        return False, ""

    # Bypass structured JSON feeds (API endpoints or JSON dumps)
    if content.lstrip().startswith(("{", "[")):
        return False, ""

    lines = content.splitlines()[:15]
    header_text = "\n".join(lines)

    years_found = [int(m.group(1)) for m in re.finditer(r"\b(20\d{2})\b", header_text)]
    has_active_cycle = any(y >= current_year for y in years_found)

    # Check for prior/expired cycle years (< current_year)
    past_years = [y for y in years_found if y < current_year and y >= 2000]
    if past_years and not has_active_cycle:
        past_year = past_years[0]
        return True, f"Upstream feed header specifies expired {past_year} cycle without active {current_year}+ updates."

    # Check for explicit maintainer abandonment or archival keywords
    abandoned_match = re.search(r"\b(abandoned|archived|deprecated|no longer maintained)\b", header_text, re.IGNORECASE)
    if abandoned_match and not has_active_cycle:
        return True, "Upstream feed is explicitly marked as abandoned or archived by maintainers."

    return False, ""


def filter_candidate_links(candidates: list, checker_func=None, max_workers: int = 8) -> list:
    """
    Probes application URLs of candidates using concurrent HTTP checks,
    weeding out dead links, generic ATS redirects, and expired application windows,
    while enriching active candidates with verified position type and hours.
    """
    if not candidates:
        return []

    def _safe_check(opp):
        raw_url = opp.get("apply_url")
        if not raw_url:
            return opp, False, "Missing URL"

        # Check if caller provided an explicit checker_func
        if checker_func is not None:
            try:
                res = checker_func(opp)
                if isinstance(res, tuple) and len(res) == 3:
                    return res
                return opp, True, "Unknown checker response format"
            except Exception as exc:
                return opp, True, f"Checker exception/skip: {exc}"

        # 1. Prefer deep inspection via ats_scraper directly if available
        if ats_scraper is not None and hasattr(ats_scraper, "inspect_job_page"):
            try:
                info = ats_scraper.inspect_job_page(raw_url, timeout=10)
                if not info["is_active"]:
                    return opp, False, info["reason"]

                # Check ATS catalog redirect if resolved_url present
                resolved_url = info.get("resolved_url") or raw_url
                if is_ats_redirected_to_catalog is not None:
                    is_red, red_reason = is_ats_redirected_to_catalog(raw_url, resolved_url)
                    if is_red:
                        return opp, False, red_reason

                # Enrich active candidate
                opp["position_type"] = info.get("position_type", "Unspecified")
                opp["hours_per_week"] = info.get("hours_per_week", "Standard Internship Hours")
                return opp, True, info.get("reason", "Active (200 OK)")
            except Exception as e:
                return opp, True, f"Checker exception/skip: {e}"

        # 2. Fall back to check_single_link only if ats_scraper is None
        if check_single_link is not None:
            try:
                res = check_single_link(opp)
                if isinstance(res, tuple) and len(res) == 3:
                    return res
                return opp, True, "Unknown checker response format"
            except Exception as exc:
                return opp, True, f"Checker exception/skip: {exc}"

        return opp, True, "Active (unverified)"

    verified = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_safe_check, candidates))

    for opp, is_active, reason in results:
        if is_active:
            verified.append(opp)
        else:
            print(f"  [DISQUALIFIED] {opp.get('company')} - {opp.get('role')} ({reason})", file=sys.stderr)

    return verified


def main():
    parser = argparse.ArgumentParser(description="Unified Opportunities Scanner with Dynamic Worldwide Location & Constraints Engine.")
    parser.add_argument("--days", type=int, default=7, help="Maximum age of job postings in days (default: 7)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum candidates to export to pending_scan.json (default: 10)")
    parser.add_argument("--source", type=str, default=None, help="Filter to run only a specific source ID")
    parser.add_argument("--all", action="store_true", help="Include all candidates without limiting batch size")
    parser.add_argument("--verify-links", action="store_true", help="Probe candidate apply_url to drop 404s and corporate ATS redirects before export.")
    args = parser.parse_args()

    profile = load_candidate_profile()
    print("=======================================================")
    print("Unified Opportunities Scanner (Dynamic Candidate Engine)")
    print(f"Candidate: {profile.name}")
    print(f"Home Location: {profile.raw_location} -> {profile.home_display}")
    print(f"US Authorization: {profile.work_authorization} (US Authorized: {profile.is_us_authorized})")
    print(f"Disallowed Industries: {', '.join(profile.disallowed_industries)}")
    print("=======================================================")

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
            stale, reason = is_stale_upstream_feed(content)
            if stale:
                print(f"  [SKIP] Skipping stale source '{src['id']}': {reason}", file=sys.stderr)
                continue
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

            score, tier = score_and_tier(p, profile)
            if score > 0:
                p["viability_score"] = score
                p["tier_category"] = tier
                all_candidates.append(p)

    # Sort candidates by viability score (descending), then age (ascending)
    all_candidates.sort(key=lambda x: (-x["viability_score"], x["age_days"]))

    limit = len(all_candidates) if args.all else args.limit
    selected = all_candidates[:limit]

    if getattr(args, "verify_links", False):
        print(f"\nVerifying live links for top {len(selected)} candidate roles...")
        selected = filter_candidate_links(selected)
        print(f"Retained {len(selected)} verified active opportunities.")

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

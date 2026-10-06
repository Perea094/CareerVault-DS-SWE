from __future__ import annotations

import os
import sys
import json
import csv
import argparse
import re
from pathlib import Path
from datetime import datetime

# Path setup
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from scan_opportunities import CandidateProfile, score_and_tier, load_candidate_profile
from prune_opportunities import check_single_link, sync_csv, CSV_FIELDS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database", "opportunities.json")
CSV_PATH = os.path.join(BASE_DIR, "database", "opportunities.csv")
PENDING_PATH = os.path.join(BASE_DIR, "database", "pending_scan.json")


def slugify(company: str, role: str, numeric_id: int) -> str:
    """
    Generate standard opportunity ID slug: opp-XX-company-role.
    Numeric IDs are 2-digit zero-padded for IDs < 100.
    """
    combined = f"{company or ''} {role or ''}".strip()
    cleaned = re.sub(r'[^a-zA-Z0-9]+', '-', combined.lower()).strip('-')
    cleaned = re.sub(r'-+', '-', cleaned)
    try:
        n = int(numeric_id)
        num_str = f"{n:02d}"
    except (ValueError, TypeError):
        num_str = str(numeric_id)
    return f"opp-{num_str}-{cleaned}" if cleaned else f"opp-{num_str}"


def _parse_tier_number(tier) -> int:
    """Extract integer tier number (1..5) from various tier representations."""
    if isinstance(tier, int):
        return tier
    tier_str = str(tier)
    m = re.search(r'\btier\s*(\d)\b', tier_str, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m2 = re.search(r'\b(\d)\b', tier_str)
    if m2:
        return int(m2.group(1))
    return 5


def estimate_success_ratio(
    tier,
    profile: CandidateProfile = None,
    role: str = "",
    loc: str = ""
) -> tuple[str, float, float, str]:
    """
    Estimate success ratio range (string, min_float, max_float, justification)
    grounded in candidate profile, location, and role tier:
    - Tier 1: 85% - 95%
    - Tier 2: 65% - 80% (or 45% - 60% for new grad roles requiring coursework balance)
    - Tier 3: 25% - 45% (or 20% - 40% for quant)
    - Tier 4: 35% - 50%
    - Tier 5: 15% - 30% (deprioritized due to unverified visa policy)
    """
    t_num = _parse_tier_number(tier)
    role_lower = (role or "").lower()
    loc_lower = (loc or "").lower()

    if t_num == 1:
        home_disp = getattr(profile, "home_display", "Home Market") if profile else "Home Market"
        return (
            "85% - 95%",
            0.85,
            0.95,
            f"Direct legal match in {home_disp} with zero visa friction and maximum employer viability."
        )

    elif t_num == 2:
        is_new_grad = any(k in role_lower for k in ["new grad", "graduate", "full-time", "full time", "associate"]) or "full-time" in loc_lower
        if is_new_grad:
            return (
                "45% - 60%",
                0.45,
                0.60,
                "Remote arrangement matches location flexibility; requires verifying if full-time post-grad commitment can be scheduled around university coursework."
            )
        else:
            return (
                "65% - 80%",
                0.65,
                0.80,
                "Direct fit with remote preference and student schedule (20-30 hrs/week); high alignment with verified technical competencies."
            )

    elif t_num == 3:
        is_quant = any(k in role_lower for k in ["quant", "quantitative", "trading", "algorithmic"])
        if is_quant:
            return (
                "20% - 40%",
                0.20,
                0.40,
                "Elite quantitative trading / research role with intensive mathematical, statistical, and algorithmic screening."
            )
        else:
            return (
                "25% - 45%",
                0.25,
                0.45,
                "Top-tier employer with documented J-1/H-1B visa sponsorship; rigorous algorithmic, statistical, and ML system screening bar."
            )

    elif t_num == 4:
        return (
            "35% - 50%",
            0.35,
            0.50,
            "Canadian co-op / international hub opportunity; requires Canadian study/work permit or international youth mobility bilateral agreement."
        )

    else:  # Tier 5 or default
        return (
            "15% - 30%",
            0.15,
            0.30,
            "Deprioritized due to unverified visa policy in domestic US market; potential barrier if company does not sponsor international student visas."
        )


def enrich_candidate(cand: dict, profile: CandidateProfile = None, numeric_id: int = 1) -> dict:
    """
    Enrich a raw candidate into complete schema dictionary matching opportunities.json.
    """
    if profile is None:
        profile = load_candidate_profile()
    elif isinstance(profile, dict):
        profile = CandidateProfile(
            name=profile.get("name", "Candidate"),
            location=profile.get("location") or profile.get("current_location", "City, Country"),
            work_authorization=profile.get("work_authorization") or profile.get("us_work_authorization", "None"),
            disallowed_industries=profile.get("disallowed_industries", ["crypto", "web3"]),
            target_hours=profile.get("target_hours", "20-30")
        )

    company = (cand.get("company") or "Unknown").strip()
    role = (cand.get("role") or "Software / Data Role").strip()
    location = (cand.get("location") or "Unspecified").strip()

    # Determine tier
    tier = cand.get("tier") or cand.get("tier_category")
    if not tier:
        item_copy = dict(cand)
        item_copy.setdefault("company", company)
        item_copy.setdefault("role", role)
        item_copy.setdefault("location", location)
        _, tier = score_and_tier(item_copy, profile)

    # Slug ID
    slug_id = cand.get("id") or slugify(company, role, numeric_id)

    # Work arrangement & hours
    role_lower = role.lower()
    is_new_grad = any(k in role_lower for k in ["new grad", "graduate", "full-time", "full time", "associate"])

    pos_type = cand.get("position_type")
    if cand.get("work_arrangement"):
        work_arrangement = cand["work_arrangement"]
    elif pos_type and "full-time" in pos_type.lower():
        work_arrangement = "Full-Time / New Grad"
    elif is_new_grad:
        work_arrangement = "Full-Time / New Grad"
    else:
        work_arrangement = "Internship / Co-op"

    if cand.get("hours_per_week"):
        hours_per_week = cand["hours_per_week"]
    elif "full-time" in work_arrangement.lower():
        hours_per_week = "Full-Time (40 hrs/week)"
    else:
        hours_per_week = f"{getattr(profile, 'target_hours', '20-30')} hrs/week"

    # Compensation
    compensation = cand.get("compensation") or cand.get("salary")
    if not compensation or compensation == "Not specified":
        if "full-time" in work_arrangement.lower():
            compensation = "$90,000 - $135,000 / yr"
        else:
            compensation = "$45 - $65 / hr"

    # Realistic Success Ratio
    ratio_str, min_val, max_val, justification = estimate_success_ratio(tier, profile, role, location)
    if cand.get("realistic_success_ratio"):
        ratio_str = cand["realistic_success_ratio"]
    if cand.get("success_ratio_min") is not None:
        min_val = cand["success_ratio_min"]
    if cand.get("success_ratio_max") is not None:
        max_val = cand["success_ratio_max"]
    if cand.get("success_ratio_justification"):
        justification = cand["success_ratio_justification"]

    # Urgency
    if cand.get("urgency"):
        urgency = cand["urgency"]
    elif cand.get("age_days", 999) <= 2 or "urgent" in str(cand.get("age", "")).lower():
        urgency = "⚠️ URGENT (Posted < 24-48h)"
    else:
        urgency = "Standard Application Window"

    # Strategic Action
    if cand.get("strategic_action"):
        strategic_action = cand["strategic_action"]
    elif "Tier 1" in tier:
        strategic_action = "Prioritize Direct Application in Local Hub"
    elif "Tier 2" in tier and "Full-Time" in hours_per_week:
        strategic_action = "Review Full-Time vs Part-Time Schedule Compatibility"
    elif "Tier 2" in tier:
        strategic_action = "Prioritize Flexible Remote Application with Grounded Projects"
    elif "Tier 3" in tier:
        strategic_action = "Target Early Application & Prepare Technical Screen"
    elif "Tier 4" in tier:
        strategic_action = "Verify Work Permit / Co-op Eligibility"
    else:
        strategic_action = "Monitor Application Status & Verify Sponsorship"

    source_repo = cand.get("source_repo") or cand.get("source_name") or cand.get("source_id") or "Direct Ingestion"
    apply_url = (cand.get("apply_url") or "").strip()
    status = cand.get("status", "eligible")
    application_status = cand.get("application_status", "wishlist")

    vault_folder = "eligible" if status == "eligible" else "non-eligible"
    vault_note = cand.get("vault_note") or f"004-work-opportunities/{vault_folder}/{slug_id}.md"

    # Skills and highlights
    is_swe = any(k in role_lower for k in ["software", "swe", "frontend", "backend", "full stack", "fullstack", "devops"])
    if cand.get("key_points_to_highlight"):
        highlights = cand["key_points_to_highlight"]
    elif is_swe:
        highlights = [
            "Align core software engineering competencies: Python/C++/Java, data structures, algorithms, and modular system design.",
            "Highlight production system rigor: automated unit/integration testing, CI/CD pipelines, and clean API design.",
            "[ACTION REQUIRED] Document verified projects in 001-background/projects/ to provide concrete metric evidence."
        ]
    else:
        highlights = [
            "Align core data science competencies: Python (NumPy, pandas, Scikit-Learn), exploratory data analysis, and predictive modeling.",
            "Highlight mathematical and statistical rigor: hypothesis testing, regression analysis, and evaluation metrics (AUC-ROC, F1, RMSE).",
            "[ACTION REQUIRED] Document verified projects in 001-background/projects/ to provide concrete metric evidence."
        ]

    if cand.get("key_considerations"):
        considerations = cand["key_considerations"]
    else:
        legal_text = (
            "Domestic authorization verified."
            if getattr(profile, "is_us_authorized", False)
            else "Requires visa sponsorship for international relocation or remote contractor / local entity arrangement."
        )
        considerations = [
            f"Work style: {location}",
            "Candidate status: Junior standing, B.S. in Computer Science / Data Science (Graduation: May 2027)",
            f"Legal constraint: {legal_text}"
        ]

    if cand.get("missing_or_bridge_skills"):
        missing_skills = cand["missing_or_bridge_skills"]
    elif is_swe:
        missing_skills = [
            "Distributed Systems / Microservices architecture",
            "Cloud Infrastructure (AWS / GCP / Docker / Kubernetes)",
            "System Design and High-concurrency performance profiling"
        ]
    else:
        missing_skills = [
            "Production MLOps / Cloud Deployment (AWS SageMaker / GCP Vertex AI / Docker)",
            "Distributed Computing / Big Data pipelines (PySpark / SQL at scale)",
            "Experimentation platforms (A/B testing, causal inference in production)"
        ]

    today_str = datetime.now().strftime("%Y-%m-%d")

    return {
        "id": slug_id,
        "numeric_id": int(numeric_id),
        "company": company,
        "role": role,
        "tier": tier,
        "location": location,
        "work_arrangement": work_arrangement,
        "hours_per_week": hours_per_week,
        "compensation": compensation,
        "realistic_success_ratio": ratio_str,
        "success_ratio_min": min_val,
        "success_ratio_max": max_val,
        "success_ratio_justification": justification,
        "urgency": urgency,
        "strategic_action": strategic_action,
        "source_repo": source_repo,
        "apply_url": apply_url,
        "file_reference": cand.get("file_reference", ""),
        "vault_note": vault_note,
        "status": status,
        "application_status": application_status,
        "key_points_to_highlight": highlights,
        "key_considerations": considerations,
        "pros": cand.get("pros") or [
            f"Strong domain focus: {role}",
            "High-signal technical exposure and portfolio acceleration",
            f"Discovered via verified upstream feed: {source_repo}"
        ],
        "cons": cand.get("cons") or [
            "Competitive candidate pool requiring sharp technical interview execution."
        ],
        "missing_or_bridge_skills": missing_skills,
        "date_identified": cand.get("date_identified", today_str),
        "last_audited": cand.get("last_audited", today_str)
    }


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    return url.strip().rstrip("/").lower()


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'[^a-zA-Z0-9]+', '', text.lower())


def sync_database(
    new_candidates: list[dict],
    db_path: str = DB_PATH,
    csv_path: str = CSV_PATH,
    profile: CandidateProfile = None,
    verify_links: bool = True
) -> int:
    """
    Merge new candidate records into the opportunities database:
    - Deduplicates by apply_url and normalized (company, role).
    - Optionally verifies application links.
    - Assigns sequential numeric IDs starting after max existing ID.
    - Writes updated database to db_path (JSON) and csv_path (CSV).
    - Returns count of newly added opportunities.
    """
    if profile is None:
        profile = load_candidate_profile()

    db_data = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except Exception as e:
            print(f"[WARN] Error loading {db_path}: {e}", file=sys.stderr)

    if not isinstance(db_data, dict):
        db_data = {}

    if "opportunities" not in db_data or not isinstance(db_data["opportunities"], list):
        db_data["opportunities"] = []

    # Collect existing keys for deduplication
    existing_urls = set()
    existing_pairs = set()

    for opp in db_data["opportunities"]:
        u = _normalize_url(opp.get("apply_url"))
        if u:
            existing_urls.add(u)
        c = _normalize_text(opp.get("company"))
        r = _normalize_text(opp.get("role"))
        if c and r:
            existing_pairs.add((c, r))

    # Also check archived opportunities if available
    archive_path = os.path.join(os.path.dirname(os.path.abspath(db_path)), "archived_opportunities.json")
    if os.path.exists(archive_path):
        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                arch_data = json.load(f)
                for opp in arch_data.get("opportunities", []):
                    u = _normalize_url(opp.get("apply_url"))
                    if u:
                        existing_urls.add(u)
                    c = _normalize_text(opp.get("company"))
                    r = _normalize_text(opp.get("role"))
                    if c and r:
                        existing_pairs.add((c, r))
        except Exception:
            pass

    # Deduplicate incoming candidates
    valid_new = []
    for cand in new_candidates:
        u = _normalize_url(cand.get("apply_url"))
        c = _normalize_text(cand.get("company"))
        r = _normalize_text(cand.get("role"))

        if u and u in existing_urls:
            continue
        if c and r and (c, r) in existing_pairs:
            continue

        if u:
            existing_urls.add(u)
        if c and r:
            existing_pairs.add((c, r))

        valid_new.append(cand)

    # Optional Link Verification
    if verify_links and valid_new:
        verified_candidates = []
        for cand in valid_new:
            try:
                res = check_single_link(cand)
                is_active = res[1] if isinstance(res, tuple) and len(res) >= 2 else True
            except Exception:
                is_active = True
            if is_active:
                verified_candidates.append(cand)
        valid_new = verified_candidates

    if not valid_new:
        if csv_path and not os.path.exists(csv_path):
            try:
                sync_csv(db_data["opportunities"], csv_path=csv_path)
            except TypeError:
                pass
        return 0

    # Max existing numeric ID
    max_id = max([o.get("numeric_id", 0) for o in db_data["opportunities"]] or [0])

    for cand in valid_new:
        max_id += 1
        enriched = enrich_candidate(cand, profile, max_id)
        db_data["opportunities"].append(enriched)

    # Update metadata
    today_str = datetime.now().strftime("%Y-%m-%d")
    db_data["total_records"] = len(db_data["opportunities"])
    db_data["last_updated"] = today_str
    if "candidate" not in db_data:
        db_data["candidate"] = {
            "name": getattr(profile, "name", "Candidate"),
            "location": getattr(profile, "raw_location", "City, Country"),
            "us_work_authorization": getattr(profile, "work_authorization", "None"),
            "target_hours_per_week": getattr(profile, "target_hours", "20-30 hrs/week"),
            "preferences_source": "001-background/preferences.md"
        }

    # Save JSON database
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=2, ensure_ascii=False)

    # Sync CSV
    if csv_path:
        os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
        try:
            sync_csv(db_data["opportunities"], csv_path=csv_path)
        except TypeError:
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, lineterminator="\n")
                writer.writeheader()
                for o in db_data["opportunities"]:
                    writer.writerow({
                        "ID": o.get("id", ""),
                        "Numeric_ID": o.get("numeric_id", ""),
                        "Company": o.get("company", ""),
                        "Role": o.get("role", ""),
                        "Tier": o.get("tier", ""),
                        "Location": o.get("location", ""),
                        "Work_Arrangement": o.get("work_arrangement", ""),
                        "Hours_Per_Week": o.get("hours_per_week", ""),
                        "Compensation": o.get("compensation", ""),
                        "Realistic_Success_Ratio": o.get("realistic_success_ratio", ""),
                        "Urgency": o.get("urgency", ""),
                        "Strategic_Action": o.get("strategic_action", ""),
                        "Status": o.get("status", ""),
                        "Application_Status": o.get("application_status", ""),
                        "Apply_URL": o.get("apply_url", ""),
                        "Vault_Note": o.get("vault_note", ""),
                        "Key_Highlights_Summary": " | ".join(o.get("key_points_to_highlight", []) or []),
                        "Missing_Skills_Summary": " | ".join(o.get("missing_or_bridge_skills", []) or [])
                    })

    return len(valid_new)


def generate_monthly_audit(
    opportunities_data,
    output_path: str,
    profile: CandidateProfile = None,
    month_str: str | None = None
) -> str:
    """
    Generate markdown monthly audit report (opportunities-audit-YYYY-MM.md)
    with KPI breakdown across 5 tiers and top recommendations table.
    """
    if profile is None:
        profile = load_candidate_profile()

    today_str = datetime.now().strftime("%Y-%m-%d")
    if not month_str:
        month_str = datetime.now().strftime("%Y-%m")

    try:
        dt = datetime.strptime(month_str, "%Y-%m")
        month_title = dt.strftime("%B %Y")
    except Exception:
        month_title = month_str

    # Resolve opportunities list
    if isinstance(opportunities_data, (str, Path)):
        with open(opportunities_data, "r", encoding="utf-8") as f:
            data = json.load(f)
        opps = data.get("opportunities", []) if isinstance(data, dict) else data
    elif isinstance(opportunities_data, dict):
        opps = opportunities_data.get("opportunities", [])
    elif isinstance(opportunities_data, list):
        opps = opportunities_data
    else:
        opps = []

    # KPI distribution across the 5 tiers
    t1_opps = [o for o in opps if _parse_tier_number(o.get("tier")) == 1]
    t2_opps = [o for o in opps if _parse_tier_number(o.get("tier")) == 2]
    t3_opps = [o for o in opps if _parse_tier_number(o.get("tier")) == 3]
    t4_opps = [o for o in opps if _parse_tier_number(o.get("tier")) == 4]
    t5_opps = [o for o in opps if _parse_tier_number(o.get("tier")) == 5]
    total_count = len(opps)

    home_market = getattr(profile, "home_display", "Domestic Market")

    frontmatter = f"""---
created: {today_str}
updated: {today_str}
type: opportunities-audit
cycle: cycle-{month_str}
tags:
  - opportunities
  - audit
  - data-science
  - cycle-{month_str}
  - summer-2027
candidate_profile_ref: "001-background/preferences.md"
total_opportunities: {total_count}
tier_1_count: {len(t1_opps)}
tier_2_remote_count: {len(t2_opps)}
tier_3_elite_sponsors_count: {len(t3_opps)}
tier_4_canada_intl_count: {len(t4_opps)}
tier_5_general_us_count: {len(t5_opps)}
status: active
---
"""

    md_lines = [
        frontmatter,
        f"# Opportunities Audit — {month_title} (Data Science Audit Mode)",
        "",
        "## 1. Executive Summary & Audit Scope",
        f"- **Audit Cycle**: {month_title} (`cycle-{month_str}`).",
        f"- **Candidate Profile**: {getattr(profile, 'name', 'Candidate')} ({getattr(profile, 'raw_location', 'Global')}).",
        f"- **Total Verified Opportunities**: **{total_count} active roles** cataloged in database.",
        "- **Candidate Ground Truth Status**: Triaged against active constraints in [`001-background/preferences.md`](../001-background/preferences.md).",
        "",
        "---",
        "",
        "## 2. Stratified Priority Breakdown",
        "",
        "```",
        f"Total Active Opportunities ({total_count})",
        f"├── Tier 1: {home_market} ({len(t1_opps)} roles) [⭐ Direct Legal Match]",
        f"├── Tier 2: Remote & Flexible Opportunities ({len(t2_opps)} roles) [⭐ Highest Practical Fit]",
        f"├── Tier 3: Elite Target Hubs - Visa Sponsorship Track ({len(t3_opps)} roles) [🏛️ High Prestige / J-1]",
        f"├── Tier 4: Canadian Co-op & International Hubs ({len(t4_opps)} roles) [🍁 Mobility / Co-op Track]",
        f"└── Tier 5: General Domestic (Unverified Sponsorship) ({len(t5_opps)} roles) [⚠️ Unverified Visa Policy]",
        "```",
        "",
        "---",
        "",
        "## 3. High-Priority Curated Matrix",
        "",
        "| # | Company | Role | Tier / Work Style | Location | Success Ratio | Urgency | Direct Portal |",
        "| :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- |"
    ]

    matrix_rows = opps[:25] if len(opps) > 25 else opps
    for idx, o in enumerate(matrix_rows, 1):
        comp = o.get("company", "Unknown")
        role = o.get("role", "Opportunity")
        tier_str = str(o.get("tier", "Tier 2"))

        short_tier = f"Tier {_parse_tier_number(tier_str)}"
        if "remote" in tier_str.lower():
            short_tier = "Tier 2 (Remote)"
        elif "elite" in tier_str.lower() or "sponsor" in tier_str.lower():
            short_tier = "Tier 3 (Elite Sponsor)"
        elif "canada" in tier_str.lower():
            short_tier = "Tier 4 (Canada)"
        elif "tier 1" in tier_str.lower():
            short_tier = "Tier 1 (Domestic)"
        elif "tier 5" in tier_str.lower():
            short_tier = "Tier 5 (General US)"

        loc = o.get("location", "Unspecified")
        ratio = o.get("realistic_success_ratio", "50% - 65%")
        urg = o.get("urgency", "Standard")
        url = o.get("apply_url", "")
        portal_label = f"{comp} Portal"
        link_md = f"[{portal_label}]({url})" if url else "Direct Application"
        md_lines.append(f"| {idx} | **{comp}** | {role} | {short_tier} | {loc} | {ratio} | {urg} | {link_md} |")

    md_lines.extend([
        "",
        "---",
        "",
        "## 4. Deep-Dive Analysis by Priority Tier",
        "",
        f"### Tier 1: {home_market} ({len(t1_opps)} Opportunities)",
        "*Fit Justification*: Direct legal authorization with zero visa sponsorship hurdles.",
        "",
        f"### Tier 2: Remote & Flexible Opportunities ({len(t2_opps)} Opportunities)",
        "*Fit Justification*: Direct match with candidate's preference for Remote work and flexible hours accommodating student lectures.",
        "",
        f"### Tier 3: Elite Target Hubs (Visa Sponsorship Track) ({len(t3_opps)} Opportunities)",
        "*Fit Justification*: Highly competitive, but established corporate J-1 / international student visa programs make these achievable.",
        "",
        f"### Tier 4: Canadian Co-op & International Hubs ({len(t4_opps)} Opportunities)",
        "*Fit Justification*: Hubs in Toronto, Ottawa, and Montreal leveraging bilateral student exchange mobility.",
        "",
        f"### Tier 5: General Domestic (Unverified Sponsorship) ({len(t5_opps)} Opportunities)",
        "*Fit Justification*: Roles requiring individual verification of international candidate visa support.",
        "",
        "---",
        "",
        "## 5. Recruiter Gap Analysis & Strategic Action Plan",
        "",
        "> [!WARNING] Ground Truth Dependency",
        "> Tailored CVs must only reference verified background records documented under `001-background/`.",
        "",
        "### Immediate 3-Step Action Plan:",
        "1. **Document Verified Background (Step 1)**: Add verified project dossiers to `001-background/projects/`.",
        "2. **Target Tier 1 and Tier 2 Roles for Immediate Submissions (Step 2)**: Prioritize top-fit remote and direct-match opportunities.",
        "3. **Prepare for Technical Screens (Step 3)**: Review LeetCode algorithms and statistical modeling questions."
    ])

    full_markdown = "\n".join(md_lines) + "\n"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_markdown)

    return full_markdown


def main():
    parser = argparse.ArgumentParser(description="Turnkey Opportunity Database Synchronizer & Monthly Audit Generator.")
    parser.add_argument("--pending", type=str, default=PENDING_PATH, help="Path to pending scan candidates JSON.")
    parser.add_argument("--db", type=str, default=DB_PATH, help="Path to opportunities.json database.")
    parser.add_argument("--csv", type=str, default=CSV_PATH, help="Path to opportunities.csv.")
    parser.add_argument("--audit", type=str, default=None, help="Generate monthly audit markdown note to specified path.")
    parser.add_argument("--verify-links", action="store_true", help="Probe application URLs before syncing.")
    args = parser.parse_args()

    profile = load_candidate_profile()

    new_cands = []
    if os.path.exists(args.pending):
        try:
            with open(args.pending, "r", encoding="utf-8") as f:
                new_cands = json.load(f)
        except Exception as e:
            print(f"[WARN] Error reading {args.pending}: {e}", file=sys.stderr)

    print(f"[INFO] Loaded {len(new_cands)} pending candidates from {args.pending}")
    added = sync_database(new_cands, db_path=args.db, csv_path=args.csv, profile=profile, verify_links=args.verify_links)
    print(f"[SUCCESS] Synced database. Added {added} new opportunities.")

    if args.audit:
        generate_monthly_audit(args.db, args.audit, profile)
        print(f"[SUCCESS] Generated monthly audit report at {args.audit}")


if __name__ == "__main__":
    main()

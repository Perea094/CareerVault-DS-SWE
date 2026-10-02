"""AI Opportunity Audit Engine.

Audits job and internship opportunities against Diego Perea León's career preferences,
availability calendar, location constraints, visa status, and deal-breakers.
Generates structured audit results and Obsidian-compliant markdown reports.
"""

import argparse
import copy
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


def _parse_hours_range(hours_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Extract minimum and maximum hours from hours_per_week string."""
    nums = [float(x) for x in re.findall(r"\b\d+(?:\.\d+)?\b", hours_str)]
    if not nums:
        return None, None
    return min(nums), max(nums)


def audit_opportunities_against_preferences(
    preferences: Union[Dict[str, Any], Any],
    opportunities: Union[List[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Any]:
    """Audit opportunities against candidate preferences and constraints.

    Evaluates:
    - Exclusions & deal-breakers: Avoid industries (e.g., Crypto), US citizenship/security
      clearance requirements, and mandatory 5-day onsite roles during semester.
    - Location & Schedule alignment: Mexico (Querétaro, CDMX, etc.) or Remote with
      hours within candidate's target_weekly_hours_max -> Direct match.
    - Full-time schedule or international relocation: 40 hrs/week (Summer/Break) or
      US/Canadian/International roles requiring visa sponsorship -> Caution / Summer match.

    Returns:
        Structured dict with timestamp, total_analyzed, summary, matches, caution,
        and disqualified.
    """
    if hasattr(preferences, "data"):
        pref_data = preferences.data
    elif isinstance(preferences, dict):
        pref_data = preferences
    else:
        raise TypeError("preferences must be a dict or PreferenceModel instance")

    if isinstance(opportunities, dict) and "opportunities" in opportunities:
        opp_list = opportunities["opportunities"]
    elif isinstance(opportunities, list):
        opp_list = opportunities
    else:
        opp_list = []

    # Extract candidate preferences & deal-breakers
    loc_visa = pref_data.get("location_visa", {})
    us_auth = str(loc_visa.get("us_work_authorization", "None")).strip()
    has_us_auth = us_auth.lower() not in ["none", "no", "false", "", "n/a"]

    cal = pref_data.get("availability_calendar", {})
    max_weekly_hours = cal.get("target_weekly_hours_max", 30)

    ind_domain = pref_data.get("industry_domain", {})
    avoid_industries = [i.strip() for i in ind_domain.get("industries_to_avoid", []) if i.strip()]

    deal_breakers = pref_data.get("deal_breakers", {})
    hard_constraints = [c.strip() for c in deal_breakers.get("hard_constraints", []) if c.strip()]
    auto_disqualifiers = [d.strip() for d in deal_breakers.get("automatic_disqualifiers", []) if d.strip()]

    matches: List[Dict[str, Any]] = []
    caution: List[Dict[str, Any]] = []
    disqualified: List[Dict[str, Any]] = []

    for opp in opp_list:
        eval_result = _evaluate_single_opportunity(
            opp=opp,
            has_us_auth=has_us_auth,
            max_weekly_hours=max_weekly_hours,
            avoid_industries=avoid_industries,
            hard_constraints=hard_constraints,
            auto_disqualifiers=auto_disqualifiers,
        )

        category = eval_result["category"]
        item = eval_result["data"]

        if category == "matches":
            matches.append(item)
        elif category == "caution":
            caution.append(item)
        elif category == "disqualified":
            disqualified.append(item)

    total_analyzed = len(opp_list)
    return {
        "timestamp": datetime.now().isoformat(),
        "total_analyzed": total_analyzed,
        "summary": {
            "direct_matches": len(matches),
            "caution_or_summer": len(caution),
            "disqualified": len(disqualified),
        },
        "matches": matches,
        "caution": caution,
        "disqualified": disqualified,
    }


def _evaluate_single_opportunity(
    opp: Dict[str, Any],
    has_us_auth: bool,
    max_weekly_hours: int,
    avoid_industries: List[str],
    hard_constraints: List[str],
    auto_disqualifiers: List[str],
) -> Dict[str, Any]:
    """Evaluate one opportunity against active criteria."""
    opp_copy = copy.deepcopy(opp)

    company = str(opp.get("company", ""))
    role = str(opp.get("role", ""))
    location = str(opp.get("location", ""))
    hours_str = str(opp.get("hours_per_week", ""))
    tier = str(opp.get("tier", ""))
    status = str(opp.get("status", "eligible"))
    work_arr = str(opp.get("work_arrangement", ""))
    sponsorship_notes = str(opp.get("sponsorship_notes", ""))
    key_considerations = opp.get("key_considerations", [])
    cons = opp.get("cons", [])
    pros = opp.get("pros", [])

    kc_text = " ".join(key_considerations) if isinstance(key_considerations, list) else str(key_considerations)
    cons_text = " ".join(cons) if isinstance(cons, list) else str(cons)
    pros_text = " ".join(pros) if isinstance(pros, list) else str(pros)

    searchable_text = f"{company} {role} {location} {hours_str} {tier} {work_arr} {sponsorship_notes} {kc_text} {cons_text} {pros_text}".lower()

    hrs_l = hours_str.lower()
    arr_l = work_arr.lower()
    role_l = role.lower()

    is_summer = "summer" in hrs_l or "summer" in arr_l or "summer" in role_l or "break" in hrs_l

    # --- 1. Exclusions & Disqualifications ---
    disq_reasons: List[str] = []

    # Check status
    if status.lower() in ["disqualified", "ineligible", "rejected"]:
        disq_reasons.append(f"Opportunity status marked as '{status}'")

    # Check avoid industries
    for avoid in avoid_industries:
        avoid_l = avoid.lower()
        if avoid_l == "crypto":
            if (
                "crypto" in company.lower()
                or "crypto" in role.lower()
                or "web3" in company.lower()
                or "web3" in role.lower()
                or "blockchain" in company.lower()
                or "blockchain" in role.lower()
                or " crypto " in f" {searchable_text} "
                or " web3 " in f" {searchable_text} "
            ):
                disq_reasons.append(f"Industry to avoid: {avoid} (Crypto / Web3)")
        else:
            if avoid_l in company.lower() or avoid_l in role.lower() or f" {avoid_l} " in f" {searchable_text} ":
                disq_reasons.append(f"Industry to avoid: {avoid}")

    # Check US citizenship / security clearance requirements with negation guard
    negation_pattern = re.compile(
        r"\b(?:no|not|non-?)\s+(?:u\.?s\.?\s+)?citizenship\s+required\b|"
        r"\bcitizenship\s+not\s+required\b|"
        r"\bopen\s+to\s+non-?citizens\b|"
        r"\bnot\s+require\s+(?:u\.?s\.?\s+)?citizenship\b",
        re.IGNORECASE,
    )

    cit_req_patterns = [
        re.compile(r"\b(?:u\.?s\.?\s+)?citizenship\s+required\b", re.IGNORECASE),
        re.compile(r"\bmust\s+be\s+an?\s+(?:u\.?s\.?\s+)?citizen\b", re.IGNORECASE),
        re.compile(r"\b(?:u\.?s\.?\s+)?citizens?\s+only\b", re.IGNORECASE),
        re.compile(r"\bsecurity\s+clearance\s+required\b", re.IGNORECASE),
        re.compile(r"\bactive\s+security\s+clearance\b", re.IGNORECASE),
        re.compile(r"\bts/sci\b", re.IGNORECASE),
        re.compile(r"\bu\.?s\.?\s+person\s+required\b", re.IGNORECASE),
    ]

    has_cit_negation = bool(negation_pattern.search(searchable_text))
    has_cit_req = (not has_cit_negation) and any(p.search(searchable_text) for p in cit_req_patterns)

    if not has_us_auth:
        if has_cit_req:
            disq_reasons.append("US citizenship or security clearance required (no US work authorization)")
        else:
            # Check if auto_disqualifiers specifically mentions citizenship and matches affirmative patterns
            for ad in auto_disqualifiers:
                ad_l = ad.lower()
                if "citizen" in ad_l or "clearance" in ad_l:
                    if (not has_cit_negation) and any(p.search(sponsorship_notes) or p.search(kc_text) for p in cit_req_patterns):
                        disq_reasons.append(f"Automatic disqualifier: {ad}")
                        break

    # Check 5-day onsite hard constraint (with Summer Onsite Guard)
    onsite_phrases = [
        "5 days/week onsite",
        "5 days onsite",
        "onsite 5 days",
        "full-time onsite",
        "100% onsite",
    ]
    has_5day_onsite = any(p in searchable_text for p in onsite_phrases)

    no_5day_onsite = any(
        "onsite 5 days" in c.lower() or "5 days/week" in c.lower() or "5-day onsite" in c.lower()
        for c in hard_constraints
    )

    # Summer Onsite Guard: If it's a summer role, do not disqualify; route to caution_or_summer
    if no_5day_onsite and has_5day_onsite and not is_summer:
        disq_reasons.append("Mandatory 5 days/week onsite violates semester availability constraint")

    if disq_reasons:
        opp_copy["audit_status"] = "disqualified"
        opp_copy["disqualification_reasons"] = disq_reasons
        return {"category": "disqualified", "data": opp_copy}

    # --- 2. Location & Schedule Evaluation ---
    loc_l = location.lower()
    mexico_cues = [
        "mexico",
        "querétaro",
        "queretaro",
        "cdmx",
        "mexico city",
        "ciudad de méxico",
        "jalisco",
        "zapopan",
        "monterrey",
        "apodaca",
        "nuevo león",
        "nuevo leon",
    ]
    is_mexico = any(cue in loc_l for cue in mexico_cues)

    # Check remote across both location and work_arrangement
    is_remote = (
        "remote" in loc_l
        or "teletrabajo" in loc_l
        or "remote" in arr_l
        or "teletrabajo" in arr_l
        or "virtual" in arr_l
        or "work from home" in arr_l
    )

    # Dynamic Hours Evaluation against candidate's max_weekly_hours
    min_h, max_h = _parse_hours_range(hours_str)
    is_excess_hours = False
    if min_h is not None and max_h is not None:
        if min_h > max_weekly_hours:
            is_excess_hours = True
        elif max_h > max_weekly_hours:
            if not ("flexible" in hrs_l and min_h <= max_weekly_hours):
                is_excess_hours = True
    elif "40" in hrs_l or "37.5" in hrs_l or "35-40" in hrs_l:
        is_excess_hours = 40 > max_weekly_hours

    is_tier3_or_tier4 = "tier 3" in tier.lower() or "tier 4" in tier.lower()

    # General International Sponsor Fallback:
    # If not Mexico and not Remote, it's an onsite/hybrid role abroad requiring relocation sponsorship
    is_abroad_relocation = (
        is_tier3_or_tier4
        or (not is_mexico and not is_remote)
        or (not is_mexico and any(h in loc_l for h in ["hybrid", "onsite", "office", "hub"]))
    )
    requires_sponsorship = is_abroad_relocation and not has_us_auth
    is_caution_or_summer = requires_sponsorship or is_excess_hours or is_summer or has_5day_onsite

    if (is_mexico or is_remote) and not is_caution_or_summer:
        opp_copy["audit_status"] = "direct_match"
        opp_copy["match_reason"] = (
            f"Direct match: Semester-compatible hours ({hours_str} hrs/week <= {max_weekly_hours}h max) "
            "with Mexico local entity or Remote arrangement."
        )
        return {"category": "matches", "data": opp_copy}
    else:
        opp_copy["audit_status"] = "caution_or_summer"
        caution_notes: List[str] = []
        if is_summer:
            caution_notes.append("Summer break timeline (ideal for Summer 2027)")
        if is_excess_hours:
            caution_notes.append(
                f"Schedule ({hours_str} hrs/wk) exceeds current semester target max of {max_weekly_hours} hrs/wk"
            )
        if has_5day_onsite and is_summer:
            caution_notes.append("Requires 5 days/week onsite during Summer (requires relocation or local presence)")
        if requires_sponsorship:
            caution_notes.append("International role requiring visa sponsorship (US J-1, Canadian co-op work permit, or relocation sponsorship)")
        if is_remote and not is_mexico:
            caution_notes.append("International Remote: verify if entity supports Mexican contractors (W-8BEN) or requires US domestic payroll")
        opp_copy["caution_reasons"] = caution_notes
        return {"category": "caution", "data": opp_copy}


def generate_markdown_audit_report(
    audit_result: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """Generate Obsidian-compliant markdown report from audit results.

    Adheres strictly to Obsidian flat YAML frontmatter guidelines,
    providing structured executive summary, tabular breakdown, and dynamic action plan.
    """
    if output_path is None:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
        output_path = os.path.join(project_root, "004-work-opportunities", "opportunities-preference-audit.md")

    parent_dir = os.path.dirname(os.path.abspath(output_path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    summary = audit_result.get("summary", {})
    total = audit_result.get("total_analyzed", 0)
    matches = audit_result.get("matches", [])
    caution = audit_result.get("caution", [])
    disqualified = audit_result.get("disqualified", [])

    direct_matches_count = summary.get("direct_matches", len(matches))
    caution_count = summary.get("caution_or_summer", len(caution))
    disq_count = summary.get("disqualified", len(disqualified))

    today_str = datetime.now().strftime("%Y-%m-%d")

    # Flat YAML frontmatter
    frontmatter = f"""---
created: "{today_str}"
updated: "{today_str}"
type: "opportunity-audit"
tags:
  - "career/audit"
  - "opportunities"
  - "preferences"
status: "active"
total_analyzed: {total}
direct_matches: {direct_matches_count}
caution_or_summer: {caution_count}
disqualified: {disq_count}
candidate_name: "Diego Perea León"
candidate_location: "Querétaro, Mexico"
target_weekly_hours: "20-30 hrs/week"
us_work_authorization: "None"
---"""

    # Top Immediate Matches Table
    if matches:
        match_rows = []
        for m in matches:
            m_id = m.get("id", "N/A")
            co = m.get("company", "Unknown")
            role = m.get("role", "N/A")
            loc = m.get("location", "N/A")
            hrs = m.get("hours_per_week", "20-30")
            url = m.get("apply_url", "")
            action = f"[Apply]({url})" if url else "Review"
            fit = m.get("match_reason", "Semester-compatible part-time")
            match_rows.append(f"| `{m_id}` | **{co}** | {role} | {loc} | {hrs} | {fit} | {action} |")
        matches_table = "\n".join([
            "| ID | Company | Role | Location | Hours/Week | Alignment Rationale | Action |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            *match_rows,
        ])
    else:
        matches_table = "_No direct immediate matches identified._"

    # Caution / Summer Table
    if caution:
        caution_rows = []
        for c in caution:
            c_id = c.get("id", "N/A")
            co = c.get("company", "Unknown")
            role = c.get("role", "N/A")
            loc = c.get("location", "N/A")
            hrs = c.get("hours_per_week", "40")
            reasons = "<br>".join(c.get("caution_reasons", ["Summer / Sponsorship required"]))
            url = c.get("apply_url", "")
            action = f"[Apply]({url})" if url else "Review"
            caution_rows.append(f"| `{c_id}` | **{co}** | {role} | {loc} | {hrs} | {reasons} | {action} |")
        caution_table = "\n".join([
            "| ID | Company | Role | Location | Hours/Week | Key Caution / Consideration | Action |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
            *caution_rows,
        ])
    else:
        caution_table = "_No opportunities requiring caution or summer timing identified._"

    # Disqualified Table
    if disqualified:
        disq_rows = []
        for d in disqualified:
            d_id = d.get("id", "N/A")
            co = d.get("company", "Unknown")
            role = d.get("role", "N/A")
            loc = d.get("location", "N/A")
            reasons = "<br>".join(d.get("disqualification_reasons", ["Deal-breaker violation"]))
            disq_rows.append(f"| `{d_id}` | **{co}** | {role} | {loc} | {reasons} | ❌ Disqualified |")
        disq_table = "\n".join([
            "| ID | Company | Role | Location | Disqualification Reason | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
            *disq_rows,
        ])
    else:
        disq_table = "_No opportunities currently disqualified under active preferences and constraints._"

    # Dynamic Strategic Action Plan
    action_plan_lines = ["## Strategic Action Plan\n"]

    action_plan_lines.append("1. **Immediate Execution (This Week)**:")
    if matches:
        top_matches = matches[:3]
        action_plan_lines.append("   - Prioritize applications for top immediate semester matches:")
        for m in top_matches:
            co = m.get("company", "Unknown")
            role = m.get("role", "N/A")
            loc = m.get("location", "N/A")
            hrs = m.get("hours_per_week", "20-30")
            action_plan_lines.append(f"     - **{co}** (`{role}`) — {loc} ({hrs} hrs/wk)")
    else:
        action_plan_lines.append("   - _No direct semester matches currently active. Monitor upcoming requisitions._")

    action_plan_lines.append("\n2. **Summer & International Pipeline Preparation**:")
    if caution:
        top_caution = caution[:3]
        action_plan_lines.append("   - Prepare materials and verify sponsorship/schedules for key caution/summer targets:")
        for c in top_caution:
            co = c.get("company", "Unknown")
            role = c.get("role", "N/A")
            loc = c.get("location", "N/A")
            hrs = c.get("hours_per_week", "40")
            action_plan_lines.append(f"     - **{co}** (`{role}`) — {loc} ({hrs} hrs/wk)")
    else:
        action_plan_lines.append("   - _No summer or international caution opportunities currently tracked._")

    action_plan_lines.append("\n3. **Continuous Maintenance**:")
    action_plan_lines.append("   - Re-run `audit_preferences.py` whenever new opportunities are scouted or candidate preferences in `001-background/preferences.json` change.")

    action_plan_str = "\n".join(action_plan_lines)

    content = f"""{frontmatter}

# Opportunity Audit Report: Career Preferences Alignment

## Executive Summary

This automated audit systematically evaluates active job and internship requisitions against the verified career preferences, temporal availability, and deal-breakers of **Diego Perea León** (B.S. Data Science & Mathematics, Tecnológico de Monterrey).

**Active Context & Constraints**:
- **Location**: Based in Querétaro, Mexico. Local or remote arrangements preferred.
- **US Work Authorization**: None (requires J-1/TN visa sponsorship for US onsite/hybrid relocation; or W-8BEN international contractor onboarding for remote roles).
- **Academic Term Schedule**: 4th semester morning classes; target commitment is **20–30 hours/week** (weekday afternoons/evenings). 40 hours/week is reserved for Summer breaks or requires schedule flexibility.
- **Deal-Breakers**: Crypto/Web3 exclusion, no mandatory 5-day onsite during semester, and automatic exclusion of roles mandating US citizenship.

### Audit Summary Metrics

| Metric | Count | Proportion | Strategic Recommendation |
| :--- | :---: | :---: | :--- |
| **Top Immediate Matches** | **{direct_matches_count}** | {f"{(direct_matches_count / total * 100):.1f}%" if total else "0%"} | Immediate application; directly aligns with current semester schedule |
| **Summer / International Caution** | **{caution_count}** | {f"{(caution_count / total * 100):.1f}%" if total else "0%"} | Summer 2027 target pipeline & J-1 visa sponsorship verification |
| **Disqualified Opportunities** | **{disq_count}** | {f"{(disq_count / total * 100):.1f}%" if total else "0%"} | Excluded due to hard deal-breakers |
| **Total Opportunities Evaluated** | **{total}** | 100% | Evaluated against `001-background/preferences.json` |

---

## Table of Top Immediate Matches (Semester Viable: 20–30 hrs/week)

These requisitions feature **direct legal and schedule compatibility** with current semester studies. They offer part-time loads (20–30 hrs/week) or flexible student arrangements, with local Mexican corporate entities or global remote frameworks.

{matches_table}

---

## Table of Summer / International Caution Opportunities (40 hrs/week & Visa Sponsorship)

These requisitions represent high-tier opportunities that require **temporal or immigration alignment**:
1. **Schedule**: 40 hrs/week commitment suitable for Summer 2027 breaks, or requiring university agreement (*convenio de prácticas*).
2. **Immigration**: US or Canadian onsite/hybrid locations requiring J-1 / co-op visa sponsorship.
3. **Payroll**: US-remote postings requiring confirmation of international contractor (W-8BEN) hiring.

{caution_table}

---

## Table of Disqualified Opportunities

Requisitions that breach active deal-breakers (e.g., Crypto/Web3 industries, mandatory US citizenship / government security clearance, or rigid 5-day onsite requirements).

{disq_table}

---

{action_plan_str}
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def main() -> None:
    """CLI entrypoint for opportunity preference auditing."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

    default_pref = os.path.join(project_root, "001-background", "preferences.json")
    default_opps = os.path.join(project_root, "004-work-opportunities", "database", "opportunities.json")
    default_out = os.path.join(project_root, "004-work-opportunities", "opportunities-preference-audit.md")

    parser = argparse.ArgumentParser(description="Audit opportunities database against candidate preferences.")
    parser.add_argument("--preferences", "-p", default=default_pref, help="Path to preferences JSON file.")
    parser.add_argument("--opportunities", "-o", default=default_opps, help="Path to opportunities database JSON.")
    parser.add_argument("--output", "-out", default=default_out, help="Path to output markdown report.")

    args = parser.parse_args()

    # Load preferences
    if not os.path.exists(args.preferences):
        print(f"Error: Preferences file not found at {args.preferences}", file=sys.stderr)
        sys.exit(1)

    with open(args.preferences, "r", encoding="utf-8") as f:
        pref_data = json.load(f)

    # Load opportunities
    if not os.path.exists(args.opportunities):
        print(f"Error: Opportunities file not found at {args.opportunities}", file=sys.stderr)
        sys.exit(1)

    with open(args.opportunities, "r", encoding="utf-8") as f:
        opp_data = json.load(f)

    # Run audit
    audit_results = audit_opportunities_against_preferences(pref_data, opp_data)

    # Generate markdown report
    report_file = generate_markdown_audit_report(audit_results, output_path=args.output)

    summary = audit_results.get("summary", {})
    print("=" * 60)
    print("OPPORTUNITY PREFERENCE AUDIT COMPLETE")
    print("=" * 60)
    print(f"Total Evaluated:        {audit_results.get('total_analyzed', 0)}")
    print(f"Top Immediate Matches:  {summary.get('direct_matches', 0)}")
    print(f"Summer / Caution:       {summary.get('caution_or_summer', 0)}")
    print(f"Disqualified:           {summary.get('disqualified', 0)}")
    print(f"Audit Report Written:   {report_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()

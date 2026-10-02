"""Preference Data Models and Bi-Directional Markdown Synchronizer.

Provides structured data modeling for Diego Perea León's career and working
preferences, availability calendar calculations, JSON persistence, and
synchronization with flat Obsidian YAML frontmatter and narrative context notes.
"""

import copy
import json
import os
import re
from typing import Any, Dict, List, Optional, Union


DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

TIME_BLOCKS = [
    "08:00-10:00",
    "10:00-12:00",
    "12:00-14:00",
    "14:00-16:00",
    "16:00-18:00",
    "18:00-20:00",
    "20:00-22:00",
]

# Standard 2-hour schedule grid:
# Weekday afternoons (14:00-20:00) available = 6 hrs/day * 5 days = 30 hrs/wk
# Weekday mornings reserved for classes; late evenings flexible
# Weekends flexible for projects / assignments
DEFAULT_WEEKLY_GRID: Dict[str, Dict[str, str]] = {
    "Monday": {
        "08:00-10:00": "classes",
        "10:00-12:00": "classes",
        "12:00-14:00": "unavailable",
        "14:00-16:00": "available",
        "16:00-18:00": "available",
        "18:00-20:00": "available",
        "20:00-22:00": "flexible",
    },
    "Tuesday": {
        "08:00-10:00": "classes",
        "10:00-12:00": "classes",
        "12:00-14:00": "unavailable",
        "14:00-16:00": "available",
        "16:00-18:00": "available",
        "18:00-20:00": "available",
        "20:00-22:00": "flexible",
    },
    "Wednesday": {
        "08:00-10:00": "classes",
        "10:00-12:00": "classes",
        "12:00-14:00": "unavailable",
        "14:00-16:00": "available",
        "16:00-18:00": "available",
        "18:00-20:00": "available",
        "20:00-22:00": "flexible",
    },
    "Thursday": {
        "08:00-10:00": "classes",
        "10:00-12:00": "classes",
        "12:00-14:00": "unavailable",
        "14:00-16:00": "available",
        "16:00-18:00": "available",
        "18:00-20:00": "available",
        "20:00-22:00": "flexible",
    },
    "Friday": {
        "08:00-10:00": "classes",
        "10:00-12:00": "classes",
        "12:00-14:00": "unavailable",
        "14:00-16:00": "available",
        "16:00-18:00": "available",
        "18:00-20:00": "available",
        "20:00-22:00": "flexible",
    },
    "Saturday": {
        "08:00-10:00": "unavailable",
        "10:00-12:00": "flexible",
        "12:00-14:00": "flexible",
        "14:00-16:00": "flexible",
        "16:00-18:00": "flexible",
        "18:00-20:00": "unavailable",
        "20:00-22:00": "unavailable",
    },
    "Sunday": {
        "08:00-10:00": "unavailable",
        "10:00-12:00": "flexible",
        "12:00-14:00": "flexible",
        "14:00-16:00": "flexible",
        "16:00-18:00": "flexible",
        "18:00-20:00": "unavailable",
        "20:00-22:00": "unavailable",
    },
}

DEFAULT_PREFERENCES: Dict[str, Any] = {
    "candidate": {
        "name": "Diego Perea León",
        "university": "Tecnológico de Monterrey",
        "degree": "B.S. Data Science & Mathematics",
        "current_semester": "4th semester",
        "expected_graduation": "2027",
    },
    "metadata": {
        "created": "2026-07-01",
        "updated": "2026-10-02",
        "type": "preferences",
        "tags": [
            "background",
            "preferences",
            "constraints",
        ],
        "status": "active",
        "version": "1.1",
        "source": "User interview via opencode session",
        "privacy": "Contains personal work preferences — not for public sharing",
    },
    "academic_context": {
        "university": "Tecnológico de Monterrey",
        "program": "B.S. Data Science & Mathematics",
        "term": "4th semester",
        "expected_graduation": "2027",
        "class_schedule_status": "Morning classes likely; schedule TBD",
        "focus_areas": ["Machine Learning", "Mathematics", "Optimization"],
    },
    "availability_calendar": {
        "preferred_hours_per_week": "20-30",
        "maximum_hours_per_week": 40,
        "weekly_grid": DEFAULT_WEEKLY_GRID,
    },
    "work_arrangement": {
        "preference_rank": [
            "Remote",
            "Hybrid",
            "Onsite",
        ],
        "hours_per_week": "20-30 (40 manageable but not preferred)",
        "hours_flexibility": True,
        "timezone_overlap": "Flexible; prefers morning availability for classes",
        "communication_style": "Both async and sync acceptable",
        "scheduling_constraints": "Morning classes likely; schedule TBD",
    },
    "location_visa": {
        "current_location": "Querétaro, Mexico",
        "us_work_authorization": "None",
        "relocation_willingness": "Remote preferred; open to international relocation if visa sponsored",
        "travel_willingness": True,
    },
    "compensation_benefits": {
        "minimum_hourly": 20,
        "equity_importance": "Don't care",
        "benefits_priorities": [
            "PTO",
            "Health insurance",
            "Learning budget",
            "Hardware stipend",
            "401k",
        ],
        "negotiation_flexibility": "Flexible",
    },
    "industry_domain": {
        "target_industries": [
            "Any (no strong preference)",
        ],
        "domains_of_interest": [
            "GenAI/LLMs",
            "RL",
            "Computer Vision",
            "NLP",
            "MLOps",
            "Research",
            "Applied ML",
        ],
        "industries_to_avoid": [
            "Crypto",
        ],
    },
    "learning_growth": {
        "mentorship": "Nice to have",
        "tech_depth_vs_breadth": "No preference",
        "conference_training_budget_expectation": "None",
        "career_trajectory": "Open",
        "skills_to_develop": [
            "Cloud ML",
            "LLM fine-tuning",
        ],
    },
    "deal_breakers": {
        "hard_constraints": [
            "No onsite 5 days/week",
            "No unpaid overtime culture",
            "Must sponsor visa for relocation",
        ],
        "toxic_signals": [
            "Vague equity promises",
            "Hero culture",
        ],
        "automatic_disqualifiers": [
            "Full-time only (no part-time/internship)",
            "Onsite required",
            "No remote option",
        ],
    },
    "role_responsibilities": {
        "ic_vs_lead": "IC preferred (not ready for lead)",
        "research_vs_engineering": "No preference",
        "team_size": "No preference",
    },
}


def _parse_slot_hours(slot_str: str) -> float:
    """Calculate slot duration in hours from a time slot string like '08:00-10:00'."""
    try:
        parts = slot_str.split("-")
        if len(parts) == 2:
            s_h, s_m = map(int, parts[0].strip().split(":"))
            e_h, e_m = map(int, parts[1].strip().split(":"))
            duration = (e_h * 60 + e_m - (s_h * 60 + s_m)) / 60.0
            if duration > 0:
                return duration
    except Exception:
        pass
    return 2.0


class PreferenceModel:
    """Structured representation of candidate career and working preferences."""

    def __init__(self, data: Optional[Union[Dict[str, Any], "PreferenceModel"]] = None):
        if data is None:
            self.data = copy.deepcopy(DEFAULT_PREFERENCES)
        elif isinstance(data, PreferenceModel):
            self.data = copy.deepcopy(data.data)
        elif isinstance(data, dict):
            self.data = copy.deepcopy(data)
        else:
            raise TypeError("data must be a dict or PreferenceModel instance")

    def calculate_available_hours(self, include_flexible: bool = False) -> float:
        """Calculate total weekly available hours from availability_calendar.weekly_grid."""
        grid = self.data.get("availability_calendar", {}).get("weekly_grid", {})
        total_hours = 0.0
        allowed_statuses = {"available", "open"}
        if include_flexible:
            allowed_statuses.update({"flexible", "preferred"})

        for day, slots in grid.items():
            if isinstance(slots, dict):
                for slot_key, status in slots.items():
                    if isinstance(status, dict):
                        stat_val = str(status.get("status", "")).lower()
                    else:
                        stat_val = str(status).lower()

                    if stat_val in allowed_statuses:
                        total_hours += _parse_slot_hours(slot_key)
            elif isinstance(slots, list):
                for item in slots:
                    if isinstance(item, dict):
                        stat_val = str(item.get("status", "")).lower()
                        if stat_val in allowed_statuses or (not stat_val and item.get("available") is True):
                            total_hours += item.get("hours", _parse_slot_hours(item.get("slot", "")))
        return total_hours

    def to_dict(self) -> Dict[str, Any]:
        """Return a deep copy of the underlying preferences dictionary."""
        return copy.deepcopy(self.data)

    def sync_to_markdown(self, md_path: str) -> None:
        """Synchronize model data to target Markdown file."""
        sync_to_markdown(self.data, md_path)


def load_preferences_json(path: str) -> Dict[str, Any]:
    """Load preference dictionary from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_preferences_json(data: Union[Dict[str, Any], PreferenceModel], path: str) -> None:
    """Save preference dictionary to JSON file."""
    if isinstance(data, PreferenceModel):
        data = data.data
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


QUOTED_LIST_KEYS = {
    "hard_constraints",
    "toxic_signals",
    "automatic_disqualifiers",
    "target_industries",
}

UNQUOTED_SCALAR_KEYS = {
    "created",
    "updated",
    "type",
    "status",
    "hours_flexibility",
    "travel_willingness",
    "minimum_hourly",
}


def _format_frontmatter_value(key: str, val: Any) -> str:
    """Format single YAML frontmatter property adhering strictly to Obsidian flat format."""
    if isinstance(val, bool):
        return f"{key}: {'true' if val else 'false'}"
    if isinstance(val, (int, float)):
        return f"{key}: {val}"
    if isinstance(val, list):
        lines = [f"{key}:"]
        should_quote = key in QUOTED_LIST_KEYS
        for item in val:
            if should_quote:
                escaped = str(item).replace('"', '\\"')
                lines.append(f'  - "{escaped}"')
            else:
                lines.append(f"  - {item}")
        return "\n".join(lines)
    # Scalar string
    str_val = str(val)
    if key in UNQUOTED_SCALAR_KEYS:
        return f"{key}: {str_val}"
    escaped = str_val.replace('"', '\\"')
    return f'{key}: "{escaped}"'


def format_flat_yaml_frontmatter(data: Dict[str, Any]) -> str:
    """Generate flat YAML frontmatter string without nested dictionaries for Obsidian."""
    meta = data.get("metadata", {})
    wa = data.get("work_arrangement", {})
    lv = data.get("location_visa", {})
    cb = data.get("compensation_benefits", {})
    ind = data.get("industry_domain", {})
    lg = data.get("learning_growth", {})
    db = data.get("deal_breakers", {})
    rr = data.get("role_responsibilities", {})

    def get_val(section: Dict[str, Any], key: str, fallback_key: Optional[str] = None, default: Any = None) -> Any:
        if key in section:
            return section[key]
        if fallback_key and fallback_key in section:
            return section[fallback_key]
        if key in data:
            return data[key]
        if fallback_key and fallback_key in data:
            return data[fallback_key]
        return default

    properties = [
        ("created", get_val(meta, "created", default="2026-07-01")),
        ("updated", get_val(meta, "updated", default="2026-10-02")),
        ("type", get_val(meta, "type", default="preferences")),
        ("tags", get_val(meta, "tags", default=["background", "preferences", "constraints"])),
        ("status", get_val(meta, "status", default="active")),
        ("version", get_val(meta, "version", default="1.1")),
        ("source", get_val(meta, "source", default="User interview via opencode session")),
        ("privacy", get_val(meta, "privacy", default="Contains personal work preferences — not for public sharing")),
        ("work_preference_rank", get_val(wa, "preference_rank", "work_preference_rank", ["Remote", "Hybrid", "Onsite"])),
        ("hours_per_week", get_val(wa, "hours_per_week", default="20-30 (40 manageable but not preferred)")),
        ("hours_flexibility", get_val(wa, "hours_flexibility", default=True)),
        ("timezone_overlap", get_val(wa, "timezone_overlap", default="Flexible; prefers morning availability for classes")),
        ("communication_style", get_val(wa, "communication_style", default="Both async and sync acceptable")),
        ("scheduling_constraints", get_val(wa, "scheduling_constraints", default="Morning classes likely; schedule TBD")),
        ("current_location", get_val(lv, "current_location", default="Querétaro, Mexico")),
        ("us_work_authorization", get_val(lv, "us_work_authorization", default="None")),
        ("relocation_willingness", get_val(lv, "relocation_willingness", default="Remote preferred; open to international relocation if visa sponsored")),
        ("travel_willingness", get_val(lv, "travel_willingness", default=True)),
        ("minimum_hourly", get_val(cb, "minimum_hourly", default=20)),
        ("equity_importance", get_val(cb, "equity_importance", default="Don't care")),
        ("benefits_priorities", get_val(cb, "benefits_priorities", default=["PTO", "Health insurance", "Learning budget", "Hardware stipend", "401k"])),
        ("negotiation_flexibility", get_val(cb, "negotiation_flexibility", default="Flexible")),
        ("target_industries", get_val(ind, "target_industries", default=["Any (no strong preference)"])),
        ("domains_of_interest", get_val(ind, "domains_of_interest", default=["GenAI/LLMs", "RL", "Computer Vision", "NLP", "MLOps", "Research", "Applied ML"])),
        ("industries_to_avoid", get_val(ind, "industries_to_avoid", default=["Crypto"])),
        ("mentorship", get_val(lg, "mentorship", default="Nice to have")),
        ("tech_depth_vs_breadth", get_val(lg, "tech_depth_vs_breadth", default="No preference")),
        ("conference_training_budget_expectation", get_val(lg, "conference_training_budget_expectation", default="None")),
        ("career_trajectory", get_val(lg, "career_trajectory", default="Open")),
        ("skills_to_develop", get_val(lg, "skills_to_develop", default=["Cloud ML", "LLM fine-tuning"])),
        ("hard_constraints", get_val(db, "hard_constraints", default=["No onsite 5 days/week", "No unpaid overtime culture", "Must sponsor visa for relocation"])),
        ("toxic_signals", get_val(db, "toxic_signals", default=["Vague equity promises", "Hero culture"])),
        ("automatic_disqualifiers", get_val(db, "automatic_disqualifiers", default=["Full-time only (no part-time/internship)", "Onsite required", "No remote option"])),
        ("ic_vs_lead", get_val(rr, "ic_vs_lead", default="IC preferred (not ready for lead)")),
        ("research_vs_engineering", get_val(rr, "research_vs_engineering", default="No preference")),
        ("team_size", get_val(rr, "team_size", default="No preference")),
    ]

    lines = []
    for k, v in properties:
        lines.append(_format_frontmatter_value(k, v))
    return "\n".join(lines)


def generate_narrative_context(data: Dict[str, Any]) -> str:
    """Generate or retrieve narrative context section in Markdown format."""
    if "narrative_context" in data and isinstance(data["narrative_context"], str) and data["narrative_context"].strip():
        narrative = data["narrative_context"].strip()
        if not narrative.startswith("# Narrative Context"):
            narrative = f"# Narrative Context (for AI assistants)\n\n{narrative}"
        return narrative

    cand = data.get("candidate", {})
    degree = cand.get("degree", "B.S. Data Science & Mathematics")
    semester = cand.get("current_semester") or cand.get("semester", "4th semester")
    university = cand.get("university", "Tecnológico de Monterrey")

    wa = data.get("work_arrangement", {})
    hours = wa.get("hours_per_week", "20-30 hours/week")

    lv = data.get("location_visa", {})
    loc = lv.get("current_location", "Querétaro, Mexico")
    us_auth = str(lv.get("us_work_authorization", "None"))
    us_auth_str = "**No US work authorization** (no OPT, H1B, TN, etc.)" if us_auth.lower() == "none" else f"**US work authorization**: {us_auth}"
    travel = "**Occasional onsite travel is acceptable**" if lv.get("travel_willingness", True) else "**No travel**"

    cb = data.get("compensation_benefits", {})
    min_h = cb.get("minimum_hourly", 20)
    eq = cb.get("equity_importance", "Don't care")
    b_prio = cb.get("benefits_priorities", ["PTO", "Health insurance", "Learning budget", "Hardware stipend", "401k"])
    b_str = " > ".join(b_prio)
    neg = cb.get("negotiation_flexibility", "Flexible")

    ind = data.get("industry_domain", {})
    domains = ind.get("domains_of_interest", ["GenAI/LLMs", "RL", "Computer Vision", "NLP", "MLOps", "Research", "Applied ML"])
    avoid = ind.get("industries_to_avoid", ["Crypto"])
    domains_str = ", ".join(domains)
    avoid_str = ", ".join(avoid)

    lg = data.get("learning_growth", {})
    ment = str(lg.get("mentorship", "Nice to have")).lower()
    traj = str(lg.get("career_trajectory", "Open")).lower()
    skills = lg.get("skills_to_develop", ["Cloud ML (AWS/Azure/GCP)", "LLM fine-tuning"])
    skills_str = " and ".join(skills)

    db = data.get("deal_breakers", {})
    h_c = db.get("hard_constraints", ["No onsite 5 days/week", "No unpaid overtime culture", "Must sponsor visa for relocation"])
    t_s = db.get("toxic_signals", ["Vague equity promises", "Hero culture"])
    a_d = db.get("automatic_disqualifiers", ["Full-time only (no part-time/internship)", "Onsite required", "No remote option"])

    rr = data.get("role_responsibilities", {})
    ic = rr.get("ic_vs_lead", "IC preferred (not ready for lead)")
    r_vs_e = rr.get("research_vs_engineering", "No preference")
    t_size = rr.get("team_size", "No preference")

    return f"""# Narrative Context (for AI assistants)

## Work Arrangement
Strong preference for **remote work** due to ongoing university studies ({degree}, {semester} at {university}). Hybrid is acceptable; onsite is last resort. Preferred commitment: **20–30 hours/week** (40 manageable but not ideal). Needs **daily hour flexibility** — can work longer on some days, shorter on others. Morning classes likely (schedule TBD), so morning availability may be limited. Comfortable with both async and sync communication.

## Location & Visa
Based in **{loc}**. {us_auth_str}. Relocation only viable with **full visa sponsorship**. Open to international relocation (Canada, EU, etc.) if sponsored. {travel}.

## Compensation & Benefits
**Minimum: ${min_h}/hour** (flexible — first formal role beyond internships). Equity: **{str(eq).lower()}**. Benefits priority order: **{b_str}**. Negotiation: **{str(neg).lower()}** — no hard floor.

## Industry & Domain
**No strong industry preference** — open to Healthcare/AI, Fintech, Research labs, Gaming, EdTech, etc. Healthcare is a growth area (no prior domain experience). **Domains of interest**: {domains_str} — **all welcome**. **Avoid: {avoid_str}**.

## Learning & Growth
Mentorship: **{ment}** (not required). No preference on tech depth vs. breadth. No conference/training budget expectation. Career trajectory: **{traj}** (IC, tech lead, research scientist, founder — all possible). **Target skills for next role**: {skills_str}.

## Deal-Breakers & Red Flags
**Hard constraints** (negotiable but strong preference): {', '.join(h_c)}.
**Toxic signals**: {', '.join(t_s)}.
**Automatic disqualifiers** (instant reject): {', '.join(a_d)}.

## Role & Responsibilities
**{ic}**. **{r_vs_e}** on research-heavy vs. engineering-heavy. **{t_size} team size preference**."""


def sync_to_markdown(data: Union[Dict[str, Any], PreferenceModel], md_path: str) -> None:
    """Generate valid flat Obsidian YAML frontmatter and narrative context into Markdown file."""
    if isinstance(data, PreferenceModel):
        data = data.data

    parent_dir = os.path.dirname(os.path.abspath(md_path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    yaml_frontmatter = format_flat_yaml_frontmatter(data)
    narrative = generate_narrative_context(data)

    content = f"---\n{yaml_frontmatter}\n---\n\n{narrative}\n"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)


def load_preferences_from_markdown(md_path: str) -> Dict[str, Any]:
    """Parse flat Obsidian YAML frontmatter and narrative context from Markdown file."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    parts = content.split("---", 2)
    frontmatter_text = ""
    narrative_text = ""
    if len(parts) >= 3:
        frontmatter_text = parts[1]
        narrative_text = parts[2].strip()

    parsed_props: Dict[str, Any] = {}
    current_list_key = None

    for line in frontmatter_text.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue
        if trimmed.startswith("- ") and current_list_key:
            val = trimmed[2:].strip().strip('"').strip("'")
            parsed_props[current_list_key].append(val)
            continue

        if ":" in trimmed:
            current_list_key = None
            colon_idx = trimmed.index(":")
            k = trimmed[:colon_idx].strip()
            v = trimmed[colon_idx + 1 :].strip()
            if not v:
                parsed_props[k] = []
                current_list_key = k
            else:
                if v.startswith('"') and v.endswith('"'):
                    parsed_props[k] = v[1:-1]
                elif v.startswith("'") and v.endswith("'"):
                    parsed_props[k] = v[1:-1]
                elif v.lower() == "true":
                    parsed_props[k] = True
                elif v.lower() == "false":
                    parsed_props[k] = False
                elif v.isdigit():
                    parsed_props[k] = int(v)
                else:
                    parsed_props[k] = v

    data = copy.deepcopy(DEFAULT_PREFERENCES)

    # Sync metadata
    for k in ["created", "updated", "type", "tags", "status", "version", "source", "privacy"]:
        if k in parsed_props:
            data["metadata"][k] = parsed_props[k]

    # Sync work arrangement
    if "work_preference_rank" in parsed_props:
        data["work_arrangement"]["preference_rank"] = parsed_props["work_preference_rank"]
    for k in ["hours_per_week", "hours_flexibility", "timezone_overlap", "communication_style", "scheduling_constraints"]:
        if k in parsed_props:
            data["work_arrangement"][k] = parsed_props[k]

    # Sync location visa
    for k in ["current_location", "us_work_authorization", "relocation_willingness", "travel_willingness"]:
        if k in parsed_props:
            data["location_visa"][k] = parsed_props[k]

    # Sync compensation
    for k in ["minimum_hourly", "equity_importance", "benefits_priorities", "negotiation_flexibility"]:
        if k in parsed_props:
            data["compensation_benefits"][k] = parsed_props[k]

    # Sync domain
    for k in ["target_industries", "domains_of_interest", "industries_to_avoid"]:
        if k in parsed_props:
            data["industry_domain"][k] = parsed_props[k]

    # Sync learning growth
    for k in ["mentorship", "tech_depth_vs_breadth", "conference_training_budget_expectation", "career_trajectory", "skills_to_develop"]:
        if k in parsed_props:
            data["learning_growth"][k] = parsed_props[k]

    # Sync deal breakers
    for k in ["hard_constraints", "toxic_signals", "automatic_disqualifiers"]:
        if k in parsed_props:
            data["deal_breakers"][k] = parsed_props[k]

    # Sync role responsibilities
    for k in ["ic_vs_lead", "research_vs_engineering", "team_size"]:
        if k in parsed_props:
            data["role_responsibilities"][k] = parsed_props[k]

    if narrative_text:
        data["narrative_context"] = narrative_text

    return data

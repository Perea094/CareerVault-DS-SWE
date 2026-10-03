"""Preference Data Models and Bi-Directional Markdown Synchronizer.

Provides structured data modeling for candidate career and working
preferences, availability calendar calculations, JSON persistence, and
synchronization with flat Obsidian YAML frontmatter and narrative context notes.
"""

import copy
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Generate 30-minute time slots from 06:00 to 22:00 (32 slots per day, 0.5 hours each)
TIME_SLOTS: List[Dict[str, Any]] = []
for _h in range(6, 22):
    _h_str = f"{_h:02d}"
    _next_h_str = f"{_h + 1:02d}"
    TIME_SLOTS.append({
        "id": f"{_h_str}_00",
        "label": f"{_h_str}:00 - {_h_str}:30",
        "hours": 0.5,
    })
    TIME_SLOTS.append({
        "id": f"{_h_str}_30",
        "label": f"{_h_str}:30 - {_next_h_str}:00",
        "hours": 0.5,
    })

# Slot IDs for university classes (08:00 to 12:00 -> 8 slots, 4h/day)
CLASS_SLOT_IDS: List[str] = [
    f"{_h:02d}_{_m}" for _h in range(8, 12) for _m in ["00", "30"]
]

# Slot IDs for available work hours (14:00 to 20:00 -> 12 slots, 6h/day, 30h/week Mon-Fri)
WORK_SLOT_IDS: List[str] = [
    f"{_h:02d}_{_m}" for _h in range(14, 20) for _m in ["00", "30"]
]

# Mapping from legacy 2-hour slots to 30-minute slots
OLD_TO_NEW_SLOT_MAP: Dict[str, List[str]] = {
    "08_10": ["08_00", "08_30", "09_00", "09_30"],
    "10_12": ["10_00", "10_30", "11_00", "11_30"],
    "12_14": ["12_00", "12_30", "13_00", "13_30"],
    "14_16": ["14_00", "14_30", "15_00", "15_30"],
    "16_18": ["16_00", "16_30", "17_00", "17_30"],
    "18_20": ["18_00", "18_30", "19_00", "19_30"],
    "20_22": ["20_00", "20_30", "21_00", "21_30"],
}


def normalize_weekly_grid(grid: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Normalize weekly grid to standard 32 30-minute slots from 06:00 to 22:00."""
    normalized: Dict[str, Dict[str, str]] = {}
    for day in DAYS:
        normalized[day] = {}
        day_input = grid.get(day, {})
        has_old_keys = any(k in OLD_TO_NEW_SLOT_MAP for k in day_input)
        if has_old_keys:
            for slot in TIME_SLOTS:
                normalized[day][slot["id"]] = "busy"
            for old_key, new_keys in OLD_TO_NEW_SLOT_MAP.items():
                status = day_input.get(old_key, "busy")
                for nk in new_keys:
                    normalized[day][nk] = status
        else:
            for slot in TIME_SLOTS:
                slot_id = slot["id"]
                normalized[day][slot_id] = day_input.get(slot_id, "busy")
    return normalized


# Generate default grid: Mon-Thu mornings are classes, Mon-Fri afternoons are available, others busy
DEFAULT_GRID: Dict[str, Dict[str, str]] = {}
for d in DAYS:
    DEFAULT_GRID[d] = {}
    for slot in TIME_SLOTS:
        slot_id = slot["id"]
        if d in ["monday", "tuesday", "wednesday", "thursday"] and slot_id in CLASS_SLOT_IDS:
            DEFAULT_GRID[d][slot_id] = "classes"
        elif d in ["monday", "tuesday", "wednesday", "thursday", "friday"] and slot_id in WORK_SLOT_IDS:
            DEFAULT_GRID[d][slot_id] = "available"
        else:
            DEFAULT_GRID[d][slot_id] = "busy"


DEFAULT_PREFERENCES: Dict[str, Any] = {
    "version": "1.1",
    "updated": "2026-10-02",
    "status": "active",
    "candidate": {
        "name": "Candidate",
        "university": "University",
        "school": "University",
        "degree": "B.S. in Computer Science / Data Science",
        "current_semester": "Junior",
        "expected_graduation": "May 2027",
        "location": "City, Country",
        "work_authorization": "Needs Sponsorship / International",
        "email_contact": "candidate@example.com",
        "email": "candidate@example.com",
        "phone": "+1 555 0100",
        "linkedin": "https://linkedin.com/in/username",
        "github": "https://github.com/username",
    },
    "metadata": {
        "created": "2026-10-02",
        "updated": "2026-10-02",
        "type": "preferences",
        "tags": [
            "background",
            "preferences",
            "constraints",
        ],
        "status": "active",
        "version": "1.1",
        "source": "Career Vault Onboarding / Preference Manager",
        "privacy": "Configure with your personal preferences",
    },
    "academic_context": {
        "university": "University",
        "program": "B.S. in Computer Science / Data Science",
        "term": "Junior",
        "expected_graduation": "May 2027",
        "class_schedule_status": "Coursework in progress",
        "focus_areas": ["Machine Learning", "Software Engineering", "Data Systems"],
    },
    "availability_calendar": {
        "time_slots": TIME_SLOTS,
        "weekly_grid": DEFAULT_GRID,
        "target_weekly_hours_min": 20,
        "target_weekly_hours_max": 30,
        "max_manageable_hours": 40,
        "schedule_notes": "Available weekday afternoons and evenings.",
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
        "current_location": "City, Country",
        "work_authorization": "Needs Sponsorship / International",
        "us_work_authorization": "None",
        "relocation_willingness": "Remote preferred; open to international relocation if visa sponsored",
        "travel_willingness": True,
    },
    "compensation_benefits": {
        "minimum_hourly": 20,
        "minimum_hourly_usd": 20,
        "equity_importance": "Don't care",
        "benefits_priorities": [
            "PTO",
            "Health insurance",
            "Learning budget",
            "Hardware stipend",
            "401k / Retirement plan",
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

        if "availability_calendar" in self.data and isinstance(self.data["availability_calendar"], dict):
            cal = self.data["availability_calendar"]
            cal["time_slots"] = copy.deepcopy(TIME_SLOTS)
            if "weekly_grid" in cal and isinstance(cal["weekly_grid"], dict):
                cal["weekly_grid"] = normalize_weekly_grid(cal["weekly_grid"])

    def calculate_available_hours(self) -> float:
        """Calculate total weekly available hours from availability_calendar.weekly_grid."""
        grid = self.data.get("availability_calendar", {}).get("weekly_grid", {})
        total = 0.0
        slots_ref = self.data.get("availability_calendar", {}).get("time_slots", TIME_SLOTS)
        slot_hours = {s["id"]: s["hours"] for s in slots_ref} if isinstance(slots_ref, list) and slots_ref and isinstance(slots_ref[0], dict) else {}

        for day, slots in grid.items():
            if isinstance(slots, dict):
                for slot_id, status in slots.items():
                    if isinstance(status, dict):
                        stat_val = str(status.get("status", "")).lower()
                    else:
                        stat_val = str(status).lower()

                    if stat_val == "available":
                        total += slot_hours.get(slot_id, 0.5)
            elif isinstance(slots, list):
                for item in slots:
                    if isinstance(item, dict):
                        stat_val = str(item.get("status", "")).lower()
                        if stat_val == "available" or (not stat_val and item.get("available") is True):
                            total += item.get("hours", 0.5)
        return total

    def to_dict(self) -> Dict[str, Any]:
        """Return a deep copy of the underlying preferences dictionary."""
        return copy.deepcopy(self.data)

    def sync_to_markdown(self, md_path: str) -> None:
        """Synchronize model data to target Markdown file."""
        sync_to_markdown(self.data, md_path)


def load_preferences_json(path: str) -> Dict[str, Any]:
    """Load preference dictionary from JSON file."""
    if not os.path.exists(path):
        return copy.deepcopy(DEFAULT_PREFERENCES)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "availability_calendar" in data and isinstance(data["availability_calendar"], dict):
        cal = data["availability_calendar"]
        cal["time_slots"] = copy.deepcopy(TIME_SLOTS)
        if "weekly_grid" in cal and isinstance(cal["weekly_grid"], dict):
            cal["weekly_grid"] = normalize_weekly_grid(cal["weekly_grid"])
    return data


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
        if not val:
            return f"{key}: []"
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
        ("updated", get_val(meta, "updated", default=data.get("updated", "2026-10-02"))),
        ("type", get_val(meta, "type", default="preferences")),
        ("tags", get_val(meta, "tags", default=["background", "preferences", "constraints"])),
        ("status", get_val(meta, "status", default=data.get("status", "active"))),
        ("version", get_val(meta, "version", default=data.get("version", "1.1"))),
        ("source", get_val(meta, "source", default="User interview via opencode session")),
        ("privacy", get_val(meta, "privacy", default="Contains personal work preferences — not for public sharing")),
        ("work_preference_rank", get_val(wa, "preference_rank", "work_preference_rank", ["Remote", "Hybrid", "Onsite"])),
        ("hours_per_week", get_val(wa, "hours_per_week", default="20-30 (40 manageable but not preferred)")),
        ("hours_flexibility", get_val(wa, "hours_flexibility", default=True)),
        ("timezone_overlap", get_val(wa, "timezone_overlap", default="Flexible; prefers morning availability for classes")),
        ("communication_style", get_val(wa, "communication_style", default="Both async and sync acceptable")),
        ("scheduling_constraints", get_val(wa, "scheduling_constraints", default="Morning classes likely; schedule TBD")),
        ("current_location", get_val(lv, "current_location", default="City, Country")),
        ("work_authorization", get_val(lv, "work_authorization", default="Needs Sponsorship / International")),
        ("us_work_authorization", get_val(lv, "us_work_authorization", default="None")),
        ("relocation_willingness", get_val(lv, "relocation_willingness", default="Remote preferred; open to international relocation if visa sponsored")),
        ("travel_willingness", get_val(lv, "travel_willingness", default=True)),
        ("minimum_hourly", get_val(cb, "minimum_hourly", default=20)),
        ("equity_importance", get_val(cb, "equity_importance", default="Don't care")),
        ("benefits_priorities", get_val(cb, "benefits_priorities", default=["PTO", "Health insurance", "Learning budget", "Hardware stipend", "401k / Retirement plan"])),
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
    acad = data.get("academic_context", {})
    degree = cand.get("degree") or acad.get("program", "B.S. in Computer Science / Data Science")
    semester = cand.get("current_semester") or cand.get("semester") or acad.get("term", "Junior")
    university = cand.get("university") or cand.get("school") or acad.get("university", "University")

    wa = data.get("work_arrangement", {})
    cal = data.get("availability_calendar", {})

    lv = data.get("location_visa", {})
    loc = lv.get("current_location", "City, Country")
    work_auth_val = str(lv.get("work_authorization") or lv.get("us_work_authorization", "Needs Sponsorship")).strip()
    if work_auth_val.lower() in ["none", "needs sponsorship", "needs sponsorship / international"]:
        work_auth_str = "**Requires visa sponsorship for US/international relocation** (or remote employment in home country)"
    else:
        work_auth_str = f"**Work authorization**: {work_auth_val}"
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
Based in **{loc}**. {work_auth_str}. Relocation only viable with **full visa sponsorship**. Open to international relocation if sponsored. {travel}.

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
**{ic}**. **{r_vs_e}** on research-heavy vs. engineering-heavy. **{t_size} on team size**."""


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


def load_preferences_from_markdown(md_path: str, base_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
            val = trimmed[2:].strip()
            if len(val) >= 2 and ((val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'"))):
                val = val[1:-1]
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
                if len(v) >= 2 and ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                    parsed_props[k] = v[1:-1]
                elif v == "[]":
                    parsed_props[k] = []
                elif v.lower() == "true":
                    parsed_props[k] = True
                elif v.lower() == "false":
                    parsed_props[k] = False
                elif v.isdigit():
                    parsed_props[k] = int(v)
                else:
                    parsed_props[k] = v

    data = copy.deepcopy(base_data if base_data is not None else DEFAULT_PREFERENCES)

    # Sync top-level version, updated, status
    if "version" in parsed_props:
        data["version"] = parsed_props["version"]
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"]["version"] = parsed_props["version"]
    if "updated" in parsed_props:
        data["updated"] = parsed_props["updated"]
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"]["updated"] = parsed_props["updated"]
    if "status" in parsed_props:
        data["status"] = parsed_props["status"]
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"]["status"] = parsed_props["status"]

    # Sync metadata
    for k in ["created", "type", "tags", "source", "privacy"]:
        if k in parsed_props:
            data.setdefault("metadata", {})[k] = parsed_props[k]

    # Sync work arrangement
    if "work_preference_rank" in parsed_props:
        data.setdefault("work_arrangement", {})["preference_rank"] = parsed_props["work_preference_rank"]
    for k in ["hours_per_week", "hours_flexibility", "timezone_overlap", "communication_style", "scheduling_constraints"]:
        if k in parsed_props:
            data.setdefault("work_arrangement", {})[k] = parsed_props[k]

    # Sync location visa
    for k in ["current_location", "us_work_authorization", "relocation_willingness", "travel_willingness"]:
        if k in parsed_props:
            data.setdefault("location_visa", {})[k] = parsed_props[k]

    # Sync compensation
    for k in ["minimum_hourly", "equity_importance", "benefits_priorities", "negotiation_flexibility"]:
        if k in parsed_props:
            data.setdefault("compensation_benefits", {})[k] = parsed_props[k]

    # Sync domain
    for k in ["target_industries", "domains_of_interest", "industries_to_avoid"]:
        if k in parsed_props:
            data.setdefault("industry_domain", {})[k] = parsed_props[k]

    # Sync learning growth
    for k in ["mentorship", "tech_depth_vs_breadth", "conference_training_budget_expectation", "career_trajectory", "skills_to_develop"]:
        if k in parsed_props:
            data.setdefault("learning_growth", {})[k] = parsed_props[k]

    # Sync deal breakers
    for k in ["hard_constraints", "toxic_signals", "automatic_disqualifiers"]:
        if k in parsed_props:
            data.setdefault("deal_breakers", {})[k] = parsed_props[k]

    # Sync role responsibilities
    for k in ["ic_vs_lead", "research_vs_engineering", "team_size"]:
        if k in parsed_props:
            data.setdefault("role_responsibilities", {})[k] = parsed_props[k]

    if narrative_text:
        data["narrative_context"] = narrative_text

    return data


# Provide alias for symmetry
sync_from_markdown = load_preferences_from_markdown

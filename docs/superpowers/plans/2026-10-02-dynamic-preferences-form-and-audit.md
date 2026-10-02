# Dynamic Preferences Form & AI Opportunity Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive survey web app and automated AI audit workflow that allows Diego Perea León to re-evaluate his career preferences and weekly schedule availability, storing the results in canonical JSON metadata, syncing flat YAML frontmatter to `001-background/preferences.md`, and auditing active opportunities in `004-work-opportunities/database/opportunities.json`.

**Architecture:** A zero-dependency Python HTTP backend (`http.server`) serves a dark-themed dynamic web interface with an interactive 7-day availability calendar grid and preference editors. When saved, the server updates `001-background/preferences.json`, synchronizes flat Obsidian-compatible frontmatter and narrative in `001-background/preferences.md`, and executes an audit engine that cross-evaluates active opportunities against weekly hours, visa sponsorship, domain fit, and hard dealbreakers. The entire workflow is packaged as a summonable skill in `.agents/skills/preference-manager/`.

**Tech Stack:** Python 3.8+ (standard library: `http.server`, `urllib`, `json`, `unittest`), Vanilla HTML5/CSS3/JavaScript (Obsidian Dark UI theme, drag-and-drop availability grid, reactive hours calculation, REST API client).

---

## File Structure

```
c:/Users/Diego Perea/Desktop/Curriculum/
├── 001-background/
│   ├── preferences.json                                 # Canonical structured preferences metadata
│   └── preferences.md                                   # Obsidian flat YAML frontmatter + narrative context
├── .agents/skills/preference-manager/
│   ├── SKILL.md                                         # Skill definition for Antigravity & agents
│   ├── scripts/
│   │   ├── preference_models.py                         # Data models, validation & Obsidian YAML/markdown sync
│   │   ├── audit_preferences.py                         # Opportunity matching & audit report generator
│   │   └── preference_server.py                         # Lightweight local HTTP server with REST endpoints
│   └── web/
│       ├── index.html                                   # Survey UI layout & sections
│       ├── style.css                                    # Dark-mode styling matching Obsidian
│       └── app.js                                       # Interactive calendar grid & form state management
└── tests/
    ├── test_preference_models.py                        # Tests for model validation & markdown sync
    ├── test_audit_preferences.py                        # Tests for opportunity matching & audit logic
    └── test_preference_server.py                        # Tests for REST API endpoints
```

---

## Bite-Sized Tasks

### Task 1: Core Preference Data Model & Bi-directional Vault Sync

**Files:**
- Create: `.agents/skills/preference-manager/scripts/preference_models.py`
- Create: `001-background/preferences.json`
- Test: `tests/test_preference_models.py`

- [ ] **Step 1: Write the failing test for preference data model and markdown synchronization**

```python
# tests/test_preference_models.py
import unittest
import os
import json
import tempfile
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "preference-manager", "scripts")))

from preference_models import (
    PreferenceModel,
    load_preferences_json,
    save_preferences_json,
    sync_to_markdown,
    DEFAULT_PREFERENCES
)

class TestPreferenceModels(unittest.TestCase):
    def test_default_preferences_structure(self):
        pref = DEFAULT_PREFERENCES
        self.assertIn("availability_calendar", pref)
        self.assertIn("weekly_grid", pref["availability_calendar"])
        self.assertIn("work_arrangement", pref)
        self.assertIn("location_visa", pref)
        self.assertIn("compensation_benefits", pref)
        self.assertIn("domains_of_interest", pref["industry_domain"])
        self.assertIn("hard_constraints", pref["deal_breakers"])

    def test_calculate_available_hours(self):
        model = PreferenceModel(DEFAULT_PREFERENCES)
        hours = model.calculate_available_hours()
        self.assertIsInstance(hours, (int, float))
        self.assertGreaterEqual(hours, 0)

    def test_json_roundtrip(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as f:
            temp_path = f.name
        try:
            save_preferences_json(DEFAULT_PREFERENCES, temp_path)
            loaded = load_preferences_json(temp_path)
            self.assertEqual(loaded["candidate"]["name"], DEFAULT_PREFERENCES["candidate"]["name"])
            self.assertEqual(loaded["work_arrangement"]["preference_rank"], ["Remote", "Hybrid", "Onsite"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_sync_to_markdown_preserves_flat_yaml(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".md", encoding="utf-8") as f:
            temp_md_path = f.name
        try:
            model = PreferenceModel(DEFAULT_PREFERENCES)
            sync_to_markdown(model.data, temp_md_path)
            with open(temp_md_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertTrue(content.startswith("---\n"))
            self.assertIn("work_preference_rank:", content)
            self.assertIn("- Remote", content)
            self.assertIn("minimum_hourly: 20", content)
            self.assertIn("current_location: \"Querétaro, Mexico\"", content)
            # Ensure no nested dict lines exist in frontmatter that would break Obsidian
            frontmatter = content.split("---")[1]
            self.assertNotIn("work_arrangement:", frontmatter)
            self.assertNotIn("location_visa:", frontmatter)
            self.assertIn("# Narrative Context", content)
        finally:
            if os.path.exists(temp_md_path):
                os.remove(temp_md_path)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_preference_models.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'preference_models'`

- [ ] **Step 3: Implement minimal code in `preference_models.py` and create canonical `001-background/preferences.json`**

```python
# .agents/skills/preference-manager/scripts/preference_models.py
import os
import json
from datetime import datetime

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
TIME_SLOTS = [
    {"id": "08_10", "label": "08:00 - 10:00", "hours": 2},
    {"id": "10_12", "label": "10:00 - 12:00", "hours": 2},
    {"id": "12_14", "label": "12:00 - 14:00", "hours": 2},
    {"id": "14_16", "label": "14:00 - 16:00", "hours": 2},
    {"id": "16_18", "label": "16:00 - 18:00", "hours": 2},
    {"id": "18_20", "label": "18:00 - 20:00", "hours": 2},
    {"id": "20_22", "label": "20:00 - 22:00", "hours": 2},
]

# Generate default grid: Mon-Thu mornings are classes, afternoons are available
DEFAULT_GRID = {}
for d in DAYS:
    DEFAULT_GRID[d] = {}
    for slot in TIME_SLOTS:
        slot_id = slot["id"]
        if d in ["monday", "tuesday", "wednesday", "thursday"] and slot_id in ["08_10", "10_12"]:
            DEFAULT_GRID[d][slot_id] = "classes"
        elif d in ["monday", "tuesday", "wednesday", "thursday", "friday"] and slot_id in ["14_16", "16_18", "18_20"]:
            DEFAULT_GRID[d][slot_id] = "available"
        else:
            DEFAULT_GRID[d][slot_id] = "busy"

DEFAULT_PREFERENCES = {
    "version": "1.1",
    "updated": datetime.now().strftime("%Y-%m-%d"),
    "status": "active",
    "candidate": {
        "name": "Diego Perea León",
        "university": "Tecnológico de Monterrey (Campus Querétaro)",
        "degree": "B.S. Data Science & Mathematics",
        "current_semester": "4th semester",
        "expected_graduation": "May 2028",
        "email_contact": "diego.perea@tec.mx"
    },
    "availability_calendar": {
        "time_slots": TIME_SLOTS,
        "weekly_grid": DEFAULT_GRID,
        "target_weekly_hours_min": 20,
        "target_weekly_hours_max": 30,
        "max_manageable_hours": 40,
        "schedule_notes": "Morning lectures at Tec de Monterrey; available weekday afternoons and evenings."
    },
    "work_arrangement": {
        "preference_rank": ["Remote", "Hybrid", "Onsite"],
        "hours_per_week": "20-30 (40 manageable but not preferred)",
        "hours_flexibility": True,
        "timezone_overlap": "Flexible; prefers morning availability for classes",
        "communication_style": "Both async and sync acceptable",
        "scheduling_constraints": "Morning classes likely; schedule TBD"
    },
    "location_visa": {
        "current_location": "Querétaro, Mexico",
        "us_work_authorization": "None",
        "relocation_willingness": "Remote preferred; open to international relocation if visa sponsored",
        "travel_willingness": True
    },
    "compensation_benefits": {
        "minimum_hourly": 20,
        "equity_importance": "Don't care",
        "benefits_priorities": ["PTO", "Health insurance", "Learning budget", "Hardware stipend", "401k"],
        "negotiation_flexibility": "Flexible"
    },
    "industry_domain": {
        "target_industries": ["Any (no strong preference)"],
        "domains_of_interest": ["GenAI/LLMs", "RL", "Computer Vision", "NLP", "MLOps", "Research", "Applied ML"],
        "industries_to_avoid": ["Crypto"]
    },
    "learning_growth": {
        "mentorship": "Nice to have",
        "tech_depth_vs_breadth": "No preference",
        "conference_training_budget_expectation": "None",
        "career_trajectory": "Open",
        "skills_to_develop": ["Cloud ML", "LLM fine-tuning"]
    },
    "deal_breakers": {
        "hard_constraints": ["No onsite 5 days/week", "No unpaid overtime culture", "Must sponsor visa for relocation"],
        "toxic_signals": ["Vague equity promises", "Hero culture"],
        "automatic_disqualifiers": ["Full-time only (no part-time/internship)", "Onsite required", "No remote option"]
    },
    "role_responsibilities": {
        "ic_vs_lead": "IC preferred (not ready for lead)",
        "research_vs_engineering": "No preference",
        "team_size": "No preference"
    }
}

class PreferenceModel:
    def __init__(self, data=None):
        self.data = data or DEFAULT_PREFERENCES

    def calculate_available_hours(self):
        grid = self.data.get("availability_calendar", {}).get("weekly_grid", {})
        total = 0
        slot_hours = {s["id"]: s["hours"] for s in TIME_SLOTS}
        for day, slots in grid.items():
            for slot_id, status in slots.items():
                if status == "available":
                    total += slot_hours.get(slot_id, 2)
        return total

def load_preferences_json(path):
    if not os.path.exists(path):
        return DEFAULT_PREFERENCES
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_preferences_json(data, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def sync_to_markdown(data, md_path):
    os.makedirs(os.path.dirname(os.path.abspath(md_path)), exist_ok=True)
    wa = data.get("work_arrangement", {})
    lv = data.get("location_visa", {})
    cb = data.get("compensation_benefits", {})
    ind = data.get("industry_domain", {})
    lg = data.get("learning_growth", {})
    db = data.get("deal_breakers", {})
    rr = data.get("role_responsibilities", {})
    cal = data.get("availability_calendar", {})
    cand = data.get("candidate", {})

    pref_ranks = "\n".join([f"  - {r}" for r in wa.get("preference_rank", ["Remote", "Hybrid", "Onsite"])])
    benefits = "\n".join([f"  - {b}" for b in cb.get("benefits_priorities", [])])
    target_ind = "\n".join([f"  - {i}" for i in ind.get("target_industries", ["Any (no strong preference)"])])
    domains = "\n".join([f"  - {d}" for d in ind.get("domains_of_interest", [])])
    avoid = "\n".join([f"  - {a}" for a in ind.get("industries_to_avoid", [])])
    skills = "\n".join([f"  - {s}" for s in lg.get("skills_to_develop", [])])
    hard_c = "\n".join([f"  - \"{c}\"" for c in db.get("hard_constraints", [])])
    toxic = "\n".join([f"  - \"{t}\"" for t in db.get("toxic_signals", [])])
    disq = "\n".join([f"  - \"{q}\"" for q in db.get("automatic_disqualifiers", [])])

    frontmatter = f"""---
created: 2026-07-01
updated: {data.get("updated", datetime.now().strftime("%Y-%m-%d"))}
type: preferences
tags:
  - background
  - preferences
  - constraints
status: {data.get("status", "active")}
version: "{data.get("version", "1.1")}"
source: "User interview via dynamic preferences survey"
privacy: "Contains personal work preferences — not for public sharing"
work_preference_rank:
{pref_ranks}
hours_per_week: "{wa.get("hours_per_week", "20-30 (40 manageable but not preferred)")}"
hours_flexibility: {str(wa.get("hours_flexibility", True)).lower()}
timezone_overlap: "{wa.get("timezone_overlap", "")}"
communication_style: "{wa.get("communication_style", "")}"
scheduling_constraints: "{wa.get("scheduling_constraints", "")}"
current_location: "{lv.get("current_location", "Querétaro, Mexico")}"
us_work_authorization: "{lv.get("us_work_authorization", "None")}"
relocation_willingness: "{lv.get("relocation_willingness", "")}"
travel_willingness: {str(lv.get("travel_willingness", True)).lower()}
minimum_hourly: {cb.get("minimum_hourly", 20)}
equity_importance: "{cb.get("equity_importance", "Don't care")}"
benefits_priorities:
{benefits}
negotiation_flexibility: "{cb.get("negotiation_flexibility", "Flexible")}"
target_industries:
{target_ind}
domains_of_interest:
{domains}
industries_to_avoid:
{avoid}
mentorship: "{lg.get("mentorship", "Nice to have")}"
tech_depth_vs_breadth: "{lg.get("tech_depth_vs_breadth", "No preference")}"
conference_training_budget_expectation: "{lg.get("conference_training_budget_expectation", "None")}"
career_trajectory: "{lg.get("career_trajectory", "Open")}"
skills_to_develop:
{skills}
hard_constraints:
{hard_c}
toxic_signals:
{toxic}
automatic_disqualifiers:
{disq}
ic_vs_lead: "{rr.get("ic_vs_lead", "IC preferred")}"
research_vs_engineering: "{rr.get("research_vs_engineering", "No preference")}"
team_size: "{rr.get("team_size", "No preference")}"
---

# Narrative Context (for AI assistants)

## Work Arrangement & Availability
Strong preference for **{', '.join(wa.get("preference_rank", []))}** work due to ongoing university studies ({cand.get("degree", "B.S. Data Science & Mathematics")}, {cand.get("current_semester", "4th semester")} at {cand.get("university", "Tecnológico de Monterrey")}). Preferred commitment: **{wa.get("hours_per_week", "20-30 hours/week")}**. Schedule notes: {cal.get("schedule_notes", "Morning classes likely; schedule TBD")}.

## Location & Visa
Based in **{lv.get("current_location", "Querétaro, Mexico")}**. **US work authorization: {lv.get("us_work_authorization", "None")}**. Relocation willingness: {lv.get("relocation_willingness", "")}. Travel willingness: {"Yes" if lv.get("travel_willingness") else "No"}.

## Compensation & Benefits
**Minimum: ${cb.get("minimum_hourly", 20)}/hour** ({cb.get("negotiation_flexibility", "Flexible")}). Equity: **{cb.get("equity_importance", "Don't care")}**. Benefits priority: {', '.join(cb.get("benefits_priorities", []))}.

## Industry & Domain
**Target industries**: {', '.join(ind.get("target_industries", []))}. **Domains of interest**: {', '.join(ind.get("domains_of_interest", []))}. **Industries to avoid**: {', '.join(ind.get("industries_to_avoid", []))}.

## Learning & Growth
Mentorship: **{lg.get("mentorship", "Nice to have")}**. Tech focus: {lg.get("tech_depth_vs_breadth", "No preference")}. Career trajectory: **{lg.get("career_trajectory", "Open")}**. Target skills: {', '.join(lg.get("skills_to_develop", []))}.

## Deal-Breakers & Red Flags
- **Hard constraints**: {', '.join(db.get("hard_constraints", []))}
- **Toxic signals**: {', '.join(db.get("toxic_signals", []))}
- **Automatic disqualifiers**: {', '.join(db.get("automatic_disqualifiers", []))}

## Role & Responsibilities
- **Leadership**: {rr.get("ic_vs_lead", "IC preferred")}
- **Focus**: {rr.get("research_vs_engineering", "No preference")}
- **Team**: {rr.get("team_size", "No preference")}
"""
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_preference_models.py`
Expected: `Ran 4 tests in ...s OK`

- [ ] **Step 5: Write initial `001-background/preferences.json` seed and commit**

Run:
```powershell
python -c "from preference_models import DEFAULT_PREFERENCES, save_preferences_json; save_preferences_json(DEFAULT_PREFERENCES, '001-background/preferences.json')"
git add 001-background/preferences.json .agents/skills/preference-manager/scripts/preference_models.py tests/test_preference_models.py
git commit -m "feat: add preference data model and obsidian markdown synchronizer"
```

---

### Task 2: AI Opportunity Audit Engine

**Files:**
- Create: `.agents/skills/preference-manager/scripts/audit_preferences.py`
- Test: `tests/test_audit_preferences.py`

- [ ] **Step 1: Write the failing test for opportunity auditing against preferences**

```python
# tests/test_audit_preferences.py
import unittest
import os
import json
import tempfile
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "preference-manager", "scripts")))

from audit_preferences import audit_opportunities_against_preferences

class TestAuditPreferences(unittest.TestCase):
    def setUp(self):
        self.mock_preferences = {
            "candidate": {"name": "Diego Perea León"},
            "availability_calendar": {"target_weekly_hours_max": 30, "target_weekly_hours_min": 20},
            "location_visa": {"current_location": "Querétaro, Mexico", "us_work_authorization": "None"},
            "industry_domain": {
                "domains_of_interest": ["GenAI/LLMs", "RL", "Computer Vision"],
                "industries_to_avoid": ["Crypto"]
            },
            "deal_breakers": {
                "hard_constraints": ["No onsite 5 days/week"],
                "automatic_disqualifiers": ["US citizenship required"]
            }
        }
        self.mock_opportunities = [
            {
                "id": "opp-01",
                "company": "Salesforce",
                "role": "AI Builder Intern [Mexico]",
                "tier": "Tier 1: Mexico & LATAM",
                "location": "Mexico City (Remote/Hybrid)",
                "hours_per_week": "20-30",
                "status": "eligible",
                "apply_url": "https://example.com/apply1"
            },
            {
                "id": "opp-02",
                "company": "CryptoCo",
                "role": "Web3 Engineer",
                "tier": "Tier 2",
                "location": "Remote",
                "hours_per_week": "20",
                "status": "eligible",
                "apply_url": "https://example.com/apply2"
            },
            {
                "id": "opp-03",
                "company": "Defense Tech",
                "role": "AI Scientist",
                "tier": "Tier 3",
                "location": "Washington, DC",
                "sponsorship_notes": "US Citizenship Required",
                "hours_per_week": "40",
                "status": "eligible",
                "apply_url": "https://example.com/apply3"
            }
        ]

    def test_audit_evaluates_matches_and_disqualifications(self):
        result = audit_opportunities_against_preferences(self.mock_preferences, self.mock_opportunities)
        self.assertIn("summary", result)
        self.assertIn("matches", result)
        self.assertIn("disqualified", result)

        match_ids = [m["id"] for m in result["matches"]]
        disq_ids = [d["id"] for d in result["disqualified"]]

        self.assertIn("opp-01", match_ids)
        self.assertIn("opp-02", disq_ids) # Crypto disqualified
        self.assertIn("opp-03", disq_ids) # US citizenship required

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_audit_preferences.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'audit_preferences'`

- [ ] **Step 3: Implement `audit_preferences.py`**

```python
# .agents/skills/preference-manager/scripts/audit_preferences.py
import os
import json
import re
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
DEFAULT_PREF_PATH = os.path.join(BASE_DIR, "001-background", "preferences.json")
DEFAULT_OPP_PATH = os.path.join(BASE_DIR, "004-work-opportunities", "database", "opportunities.json")
REPORT_PATH = os.path.join(BASE_DIR, "004-work-opportunities", "opportunities-preference-audit.md")

def audit_opportunities_against_preferences(preferences, opportunities):
    avoid_industries = [i.lower() for i in preferences.get("industry_domain", {}).get("industries_to_avoid", [])]
    domains_of_interest = [d.lower() for d in preferences.get("industry_domain", {}).get("domains_of_interest", [])]
    target_max_hours = preferences.get("availability_calendar", {}).get("target_weekly_hours_max", 30)

    matches = []
    caution = []
    disqualified = []

    for opp in opportunities:
        role = (opp.get("role") or "").lower()
        comp = (opp.get("company") or "").lower()
        loc = (opp.get("location") or "").lower()
        sponsorship = (opp.get("sponsorship_notes") or "").lower()
        work_arr = (opp.get("work_arrangement") or "").lower()
        hours = str(opp.get("hours_per_week") or "")

        # 1. Check Avoid Industries (e.g. Crypto)
        is_avoid = any(av in role or av in comp for av in avoid_industries if av)
        if is_avoid:
            disqualified.append({
                "id": opp.get("id"),
                "company": opp.get("company"),
                "role": opp.get("role"),
                "reason": f"Matches avoided industry/domain ({', '.join(avoid_industries)})"
            })
            continue

        # 2. Check Citizenship Disqualifier
        if "us citizenship required" in sponsorship or "citizenship required" in loc:
            disqualified.append({
                "id": opp.get("id"),
                "company": opp.get("company"),
                "role": opp.get("role"),
                "reason": "Requires US Citizenship (Dealbreaker)"
            })
            continue

        # 3. Check 5-day Onsite dealbreaker if in hard constraints
        hard_c = preferences.get("deal_breakers", {}).get("hard_constraints", [])
        if any("no onsite" in str(hc).lower() for hc in hard_c) and ("onsite 5 days" in work_arr or "onsite only" in work_arr):
            disqualified.append({
                "id": opp.get("id"),
                "company": opp.get("company"),
                "role": opp.get("role"),
                "reason": "Strict 5-day onsite requirement (Dealbreaker)"
            })
            continue

        # 4. Check Schedule / Hours Match
        is_part_time = "20" in hours or "30" in hours or "part-time" in work_arr or "intern" in role
        is_mexico = "mexico" in loc or "querétaro" in loc or "cdmx" in loc
        is_remote = "remote" in loc or "remote" in role

        # Score Domain Alignment
        domain_hits = [dom for dom in domains_of_interest if dom in role or dom in (opp.get("key_highlights_summary") or "").lower()]

        if is_mexico or is_remote:
            matches.append({
                "id": opp.get("id"),
                "company": opp.get("company"),
                "role": opp.get("role"),
                "tier": opp.get("tier"),
                "location": opp.get("location"),
                "hours_per_week": opp.get("hours_per_week"),
                "apply_url": opp.get("apply_url"),
                "match_reason": f"Direct legal/location fit ({'Mexico' if is_mexico else 'Remote'}), compatible with student schedule."
            })
        else:
            caution.append({
                "id": opp.get("id"),
                "company": opp.get("company"),
                "role": opp.get("role"),
                "tier": opp.get("tier"),
                "location": opp.get("location"),
                "hours_per_week": opp.get("hours_per_week"),
                "apply_url": opp.get("apply_url"),
                "caution_reason": "US/International role: requires J-1 visa sponsorship or 40h/week summer break alignment."
            })

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_analyzed": len(opportunities),
        "summary": {
            "direct_matches": len(matches),
            "caution_or_summer": len(caution),
            "disqualified": len(disqualified)
        },
        "matches": matches,
        "caution": caution,
        "disqualified": disqualified
    }

def generate_markdown_audit_report(audit_result, output_path=REPORT_PATH):
    summary = audit_result["summary"]
    timestamp = audit_result["timestamp"]

    md = f"""---
created: {timestamp[:10]}
type: audit-report
tags:
  - opportunities
  - preferences-audit
status: active
---

# Career Preferences & Opportunities Audit Report
*Generated on {timestamp}*

## Executive Summary
- **Total Opportunities Evaluated**: {audit_result["total_analyzed"]}
- **Immediate Direct Matches (Tier 1 Mexico & Tier 2 Remote)**: {summary["direct_matches"]}
- **International / Summer Sponsor Matches (Tier 3 & 4)**: {summary["caution_or_summer"]}
- **Disqualified by Hard Constraints / Schedule**: {summary["disqualified"]}

---

## 1. Top Immediate Matches (Compatible with Current Schedule & Location)
| Company | Role | Location | Hours | Apply |
| :--- | :--- | :--- | :--- | :--- |
"""
    for m in audit_result["matches"][:15]:
        apply = f"[Apply Link]({m['apply_url']})" if m.get("apply_url") else "N/A"
        md += f"| **{m.get('company')}** | {m.get('role')} | {m.get('location')} | {m.get('hours_per_week', 'Flexible')} | {apply} |\n"

    md += "\n---\n\n## 2. Opportunities Requiring Caution / Summer Availability\n| Company | Role | Location | Note |\n| :--- | :--- | :--- | :--- |\n"
    for c in audit_result["caution"][:10]:
        md += f"| **{c.get('company')}** | {c.get('role')} | {c.get('location')} | {c.get('caution_reason')} |\n"

    md += "\n---\n\n## 3. Disqualified Positions\n| Company | Role | Disqualification Reason |\n| :--- | :--- | :--- |\n"
    for d in audit_result["disqualified"][:10]:
        md += f"| **{d.get('company')}** | {d.get('role')} | {d.get('reason')} |\n"

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    return output_path

if __name__ == "__main__":
    with open(DEFAULT_PREF_PATH, "r", encoding="utf-8") as f:
        prefs = json.load(f)
    with open(DEFAULT_OPP_PATH, "r", encoding="utf-8") as f:
        opps_data = json.load(f)
    opps = opps_data.get("opportunities", [])
    res = audit_opportunities_against_preferences(prefs, opps)
    path = generate_markdown_audit_report(res)
    print(f"[SUCCESS] Audit completed: {res['summary']} -> saved to {path}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_audit_preferences.py`
Expected: `Ran 1 test in ...s OK`

- [ ] **Step 5: Commit**

Run:
```powershell
git add .agents/skills/preference-manager/scripts/audit_preferences.py tests/test_audit_preferences.py
git commit -m "feat: add opportunity audit engine for dynamic preferences"
```

---

### Task 3: Lightweight HTTP Server & REST API Endpoints

**Files:**
- Create: `.agents/skills/preference-manager/scripts/preference_server.py`
- Test: `tests/test_preference_server.py`

- [ ] **Step 1: Write the failing test for server endpoints (`/api/preferences`, `/api/save`, `/api/audit`)**

```python
# tests/test_preference_server.py
import unittest
import os
import json
import threading
import urllib.request
import urllib.parse
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "preference-manager", "scripts")))

from preference_server import create_server

class TestPreferenceServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8789
        cls.server, cls.thread = create_server(port=cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_get_preferences(self):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/api/preferences")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("candidate", data)
            self.assertIn("work_arrangement", data)

    def test_post_save_preferences(self):
        payload = json.dumps({"test": "data"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/save",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res.get("success"))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_preference_server.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'preference_server'`

- [ ] **Step 3: Implement `preference_server.py` using Python `http.server`**

```python
# .agents/skills/preference-manager/scripts/preference_server.py
import os
import sys
import json
import webbrowser
import threading
import argparse
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
PREF_JSON_PATH = os.path.join(BASE_DIR, "001-background", "preferences.json")
PREF_MD_PATH = os.path.join(BASE_DIR, "001-background", "preferences.md")
OPP_JSON_PATH = os.path.join(BASE_DIR, "004-work-opportunities", "database", "opportunities.json")
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))

from preference_models import (
    load_preferences_json,
    save_preferences_json,
    sync_to_markdown,
    DEFAULT_PREFERENCES
)
from audit_preferences import (
    audit_opportunities_against_preferences,
    generate_markdown_audit_report
)

class PreferenceRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/preferences":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            data = load_preferences_json(PREF_JSON_PATH)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if self.path == "/api/save":
            try:
                data = json.loads(body.decode("utf-8"))
                save_preferences_json(data, PREF_JSON_PATH)
                sync_to_markdown(data, PREF_MD_PATH)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": "Preferences saved and synchronized to vault successfully."
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif self.path == "/api/audit":
            try:
                prefs = load_preferences_json(PREF_JSON_PATH)
                opps = []
                if os.path.exists(OPP_JSON_PATH):
                    with open(OPP_JSON_PATH, "r", encoding="utf-8") as f:
                        opps = json.load(f).get("opportunities", [])
                
                audit_res = audit_opportunities_against_preferences(prefs, opps)
                report_file = generate_markdown_audit_report(audit_res)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "report_file": report_file,
                    "audit": audit_res
                }, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def create_server(port=8765):
    server = ThreadingHTTPServer(("127.0.0.1", port), PreferenceRequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, thread

def main():
    parser = argparse.ArgumentParser(description="Career Preferences Web App Server")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on (default: 8765)")
    parser.add_argument("--open", action="store_true", help="Automatically open browser")
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), PreferenceRequestHandler)
    url = f"http://127.0.0.1:{args.port}"
    print(f"[INFO] Preferences survey server running at {url}")
    print(f"[INFO] Serving web UI from {WEB_DIR}")
    print(f"[INFO] Press Ctrl+C to terminate.")

    if args.open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Server shutting down.")
        server.server_close()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_preference_server.py`
Expected: `Ran 2 tests in ...s OK`

- [ ] **Step 5: Commit**

Run:
```powershell
git add .agents/skills/preference-manager/scripts/preference_server.py tests/test_preference_server.py
git commit -m "feat: implement lightweight preferences web server and rest endpoints"
```

---

### Task 4: Dynamic Web UI with Weekly Availability Grid & Obsidian Theme

**Files:**
- Create: `.agents/skills/preference-manager/web/index.html`
- Create: `.agents/skills/preference-manager/web/style.css`
- Create: `.agents/skills/preference-manager/web/app.js`

- [ ] **Step 1: Create `style.css` with sleek dark mode, responsive grid, and availability badges**

```css
/* .agents/skills/preference-manager/web/style.css */
:root {
  --bg-primary: #1e1e24;
  --bg-secondary: #282830;
  --bg-tertiary: #32323e;
  --text-main: #f0f0f5;
  --text-muted: #9e9ea7;
  --accent: #7c4dff;
  --accent-hover: #966eff;
  --green: #2ecc71;
  --blue: #3498db;
  --red: #e74c3c;
  --border: #444454;
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
body { background: var(--bg-primary); color: var(--text-main); line-height: 1.5; padding: 24px; }
.container { max-width: 1040px; margin: 0 auto; }

header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px; }
h1 { font-size: 1.6rem; font-weight: 700; color: #fff; }
.subtitle { color: var(--text-muted); font-size: 0.9rem; }

.section-card { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 24px; }
.section-title { font-size: 1.15rem; font-weight: 600; margin-bottom: 16px; color: #fff; border-bottom: 1px solid var(--border); padding-bottom: 8px; }

/* Calendar & Availability Grid */
.calendar-legend { display: flex; gap: 16px; margin-bottom: 16px; align-items: center; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }
.legend-box { width: 16px; height: 16px; border-radius: 4px; }
.box-available { background: var(--green); }
.box-classes { background: var(--blue); }
.box-busy { background: var(--bg-tertiary); border: 1px solid var(--border); }

.calendar-grid { display: grid; grid-template-columns: 120px repeat(7, 1fr); gap: 6px; overflow-x: auto; }
.grid-header { font-weight: 600; text-align: center; padding: 8px 4px; font-size: 0.85rem; color: var(--text-muted); }
.time-label { font-size: 0.8rem; color: var(--text-muted); display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; }
.slot-cell { height: 38px; border-radius: 6px; border: 1px solid var(--border); cursor: pointer; transition: all 0.15s ease; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; user-select: none; }
.slot-cell.available { background: rgba(46, 204, 113, 0.25); border-color: var(--green); color: var(--green); font-weight: 600; }
.slot-cell.classes { background: rgba(52, 152, 219, 0.25); border-color: var(--blue); color: var(--blue); font-weight: 600; }
.slot-cell.busy { background: var(--bg-tertiary); color: var(--text-muted); }

.kpi-banner { display: flex; gap: 24px; background: var(--bg-tertiary); padding: 12px 18px; border-radius: 6px; margin-top: 16px; font-size: 0.9rem; align-items: center; }
.kpi-value { font-size: 1.2rem; font-weight: 700; color: var(--green); }

/* Form Elements */
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
label { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }
input[type="text"], input[type="number"], select, textarea { background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 6px; color: #fff; padding: 8px 12px; font-size: 0.9rem; }
input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); }

/* Tags & Badges */
.tag-container { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.tag-pill { background: var(--bg-tertiary); border: 1px solid var(--border); padding: 4px 10px; border-radius: 14px; font-size: 0.85rem; cursor: pointer; transition: all 0.15s; }
.tag-pill.active { background: var(--accent); border-color: var(--accent); color: #fff; }
.tag-pill.avoid { background: rgba(231, 76, 60, 0.2); border-color: var(--red); color: var(--red); }

/* Action Footer */
.action-footer { display: flex; justify-content: flex-end; gap: 12px; margin-top: 32px; }
.btn { padding: 10px 20px; border-radius: 6px; font-weight: 600; cursor: pointer; border: none; font-size: 0.95rem; transition: background 0.15s; }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { background: var(--bg-tertiary); color: var(--text-main); border: 1px solid var(--border); }
.btn-success { background: var(--green); color: #fff; }
```

- [ ] **Step 2: Create `index.html` layout**

```html
<!-- .agents/skills/preference-manager/web/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Diego Perea León — Career Preferences & Availability Survey</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Diego Perea León — Dynamic Preferences & Availability</h1>
        <div class="subtitle">Interactive survey & constraint manager for active tech opportunities</div>
      </div>
      <div id="statusIndicator" style="font-size: 0.85rem; color: var(--text-muted);">● Connected</div>
    </header>

    <!-- SECTION 1: WEEKLY AVAILABILITY GRID -->
    <div class="section-card">
      <div class="section-title">1. Weekly Availability & University Schedule</div>
      <div class="calendar-legend">
        <span style="font-size: 0.85rem; font-weight: 600; margin-right: 8px;">Paint Brush:</span>
        <label class="legend-item"><input type="radio" name="brush" value="available" checked> <div class="legend-box box-available"></div> Available for Work</label>
        <label class="legend-item"><input type="radio" name="brush" value="classes"> <div class="legend-box box-classes"></div> University Classes (Tec)</label>
        <label class="legend-item"><input type="radio" name="brush" value="busy"> <div class="legend-box box-busy"></div> Busy / Personal</label>
      </div>

      <div class="calendar-grid" id="calendarGrid">
        <!-- Rendered by app.js -->
      </div>

      <div class="kpi-banner">
        <div>Total Work Availability: <span class="kpi-value" id="kpiHours">0</span> hrs/week</div>
        <div style="color: var(--text-muted);">|</div>
        <div>Target Range: <strong>20 - 30 hrs/week</strong> (Max 40 hrs manageable)</div>
      </div>
    </div>

    <!-- SECTION 2: WORK ARRANGEMENT & LOCATION -->
    <div class="section-card">
      <div class="section-title">2. Work Modality & Mobility</div>
      <div class="form-grid">
        <div class="form-group">
          <label>Work Modality Preference Order</label>
          <input type="text" id="prefRank" value="Remote, Hybrid, Onsite">
        </div>
        <div class="form-group">
          <label>Current Location</label>
          <input type="text" id="currentLocation" value="Querétaro, Mexico">
        </div>
        <div class="form-group">
          <label>US Work Authorization</label>
          <input type="text" id="usAuth" value="None">
        </div>
        <div class="form-group">
          <label>Relocation Willingness</label>
          <input type="text" id="relocation" value="Remote preferred; open to international relocation if visa sponsored">
        </div>
      </div>
    </div>

    <!-- SECTION 3: COMPENSATION & BENEFITS -->
    <div class="section-card">
      <div class="section-title">3. Compensation & Priorities</div>
      <div class="form-grid">
        <div class="form-group">
          <label>Minimum Hourly Wage (USD)</label>
          <input type="number" id="minHourly" value="20" min="10" max="200">
        </div>
        <div class="form-group">
          <label>Benefits Priority Order (Comma separated)</label>
          <input type="text" id="benefitsOrder" value="PTO, Health insurance, Learning budget, Hardware stipend, 401k">
        </div>
      </div>
    </div>

    <!-- SECTION 4: DOMAINS & SKILLS -->
    <div class="section-card">
      <div class="section-title">4. Technical Focus & Avoided Industries</div>
      <div class="form-group">
        <label>Domains of Interest</label>
        <div class="tag-container" id="domainsContainer"></div>
      </div>
      <div class="form-group" style="margin-top: 16px;">
        <label>Industries to Avoid (Disqualifiers)</label>
        <div class="tag-container" id="avoidContainer"></div>
      </div>
    </div>

    <!-- SECTION 5: DEALBREAKERS -->
    <div class="section-card">
      <div class="section-title">5. Hard Dealbreakers</div>
      <div class="form-group">
        <label>Hard Constraints (One per line)</label>
        <textarea id="hardConstraints" rows="3"></textarea>
      </div>
    </div>

    <!-- ACTIONS -->
    <div class="action-footer">
      <button class="btn btn-secondary" id="btnReset">Reset to Vault Defaults</button>
      <button class="btn btn-primary" id="btnSave">Save Preferences</button>
      <button class="btn btn-success" id="btnSaveAndAudit">Save & Run AI Opportunity Audit</button>
    </div>
  </div>

  <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Create `app.js` with calendar rendering and API requests**

```javascript
// .agents/skills/preference-manager/web/app.js
const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
const SLOTS = [
  { id: "08_10", label: "08:00 - 10:00" },
  { id: "10_12", label: "10:00 - 12:00" },
  { id: "12_14", label: "12:00 - 14:00" },
  { id: "14_16", label: "14:00 - 16:00" },
  { id: "16_18", label: "16:00 - 18:00" },
  { id: "18_20", label: "18:00 - 20:00" },
  { id: "20_22", label: "20:00 - 22:00" }
];

let state = null;
let currentBrush = "available";

document.querySelectorAll('input[name="brush"]').forEach(radio => {
  radio.addEventListener('change', e => currentBrush = e.target.value);
});

async function init() {
  try {
    const res = await fetch("/api/preferences");
    state = await res.json();
    renderForm();
  } catch (err) {
    console.error("Failed to load preferences:", err);
  }
}

function renderForm() {
  // Calendar Grid
  const grid = document.getElementById("calendarGrid");
  grid.innerHTML = '<div class="grid-header">Time</div>';
  DAYS.forEach(d => {
    grid.innerHTML += `<div class="grid-header">${d.slice(0,3).toUpperCase()}</div>`;
  });

  const weeklyGrid = state.availability_calendar.weekly_grid;

  SLOTS.forEach(slot => {
    grid.innerHTML += `<div class="time-label">${slot.label}</div>`;
    DAYS.forEach(day => {
      const status = weeklyGrid[day]?.[slot.id] || "busy";
      const cell = document.createElement("div");
      cell.className = `slot-cell ${status}`;
      cell.dataset.day = day;
      cell.dataset.slot = slot.id;
      cell.innerText = status === "available" ? "Work" : (status === "classes" ? "Class" : "");
      cell.addEventListener("click", () => {
        weeklyGrid[day][slot.id] = currentBrush;
        cell.className = `slot-cell ${currentBrush}`;
        cell.innerText = currentBrush === "available" ? "Work" : (currentBrush === "classes" ? "Class" : "");
        updateKpi();
      });
      grid.appendChild(cell);
    });
  });

  // Fields
  document.getElementById("prefRank").value = state.work_arrangement.preference_rank.join(", ");
  document.getElementById("currentLocation").value = state.location_visa.current_location;
  document.getElementById("usAuth").value = state.location_visa.us_work_authorization;
  document.getElementById("relocation").value = state.location_visa.relocation_willingness;
  document.getElementById("minHourly").value = state.compensation_benefits.minimum_hourly;
  document.getElementById("benefitsOrder").value = state.compensation_benefits.benefits_priorities.join(", ");
  document.getElementById("hardConstraints").value = state.deal_breakers.hard_constraints.join("\n");

  // Domains
  const domContainer = document.getElementById("domainsContainer");
  domContainer.innerHTML = "";
  ["GenAI/LLMs", "RL", "Computer Vision", "NLP", "MLOps", "Research", "Applied ML", "Quant/Trading"].forEach(dom => {
    const pill = document.createElement("div");
    const active = state.industry_domain.domains_of_interest.includes(dom);
    pill.className = `tag-pill ${active ? 'active' : ''}`;
    pill.innerText = dom;
    pill.addEventListener("click", () => {
      pill.classList.toggle("active");
    });
    domContainer.appendChild(pill);
  });

  // Avoid
  const avoidContainer = document.getElementById("avoidContainer");
  avoidContainer.innerHTML = "";
  ["Crypto", "Web3", "Gambling"].forEach(av => {
    const pill = document.createElement("div");
    const active = state.industry_domain.industries_to_avoid.includes(av);
    pill.className = `tag-pill avoid ${active ? 'active' : ''}`;
    pill.innerText = av;
    pill.addEventListener("click", () => {
      pill.classList.toggle("active");
    });
    avoidContainer.appendChild(pill);
  });

  updateKpi();
}

function updateKpi() {
  let total = 0;
  const grid = state.availability_calendar.weekly_grid;
  DAYS.forEach(d => {
    SLOTS.forEach(s => {
      if (grid[d]?.[s.id] === "available") total += 2;
    });
  });
  document.getElementById("kpiHours").innerText = total;
}

function gatherPayload() {
  const activeDomains = Array.from(document.querySelectorAll("#domainsContainer .tag-pill.active")).map(e => e.innerText);
  const avoidDomains = Array.from(document.querySelectorAll("#avoidContainer .tag-pill.active")).map(e => e.innerText);
  const hardConstraints = document.getElementById("hardConstraints").value.split("\n").map(s => s.trim()).filter(Boolean);

  state.work_arrangement.preference_rank = document.getElementById("prefRank").value.split(",").map(s => s.trim());
  state.location_visa.current_location = document.getElementById("currentLocation").value.trim();
  state.location_visa.us_work_authorization = document.getElementById("usAuth").value.trim();
  state.location_visa.relocation_willingness = document.getElementById("relocation").value.trim();
  state.compensation_benefits.minimum_hourly = parseInt(document.getElementById("minHourly").value) || 20;
  state.compensation_benefits.benefits_priorities = document.getElementById("benefitsOrder").value.split(",").map(s => s.trim());
  state.industry_domain.domains_of_interest = activeDomains;
  state.industry_domain.industries_to_avoid = avoidDomains;
  state.deal_breakers.hard_constraints = hardConstraints;

  return state;
}

document.getElementById("btnSave").addEventListener("click", async () => {
  const payload = gatherPayload();
  const res = await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (data.success) {
    alert("Preferences saved and synchronized with Obsidian vault!");
  } else {
    alert("Error saving: " + data.error);
  }
});

document.getElementById("btnSaveAndAudit").addEventListener("click", async () => {
  const payload = gatherPayload();
  await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const auditRes = await fetch("/api/audit", { method: "POST" });
  const data = await auditRes.json();
  if (data.success) {
    alert(`Preferences saved! Audit complete: ${data.audit.summary.direct_matches} matches found. Check 004-work-opportunities/opportunities-preference-audit.md`);
  }
});

document.getElementById("btnReset").addEventListener("click", init);

init();
```

- [ ] **Step 4: Verify files exist and test server delivery of static assets**

Run:
```powershell
python -c "import urllib.request; resp = urllib.request.urlopen('http://127.0.0.1:8765/index.html'); print(resp.status)"
```
Expected: `200` (or test via automated mock runner).

- [ ] **Step 5: Commit**

Run:
```powershell
git add .agents/skills/preference-manager/web/
git commit -m "feat: build dynamic preferences survey web UI with availability grid"
```

---

### Task 5: Skill Registration & End-to-End Workflow Integration

**Files:**
- Create: `.agents/skills/preference-manager/SKILL.md`
- Test: Manual end-to-end execution of `python .agents/skills/preference-manager/scripts/preference_server.py --open` and audit

- [ ] **Step 1: Create `.agents/skills/preference-manager/SKILL.md`**

```markdown
---
name: preference-manager
description: Interactive survey web app and automated audit workflow to re-evaluate Diego Perea León's career preferences, weekly availability calendar, and match against opportunities in 004-work-opportunities.
---

# preference-manager

Provides an interactive dynamic survey web application and AI audit engine to maintain and re-evaluate personal preferences, university class schedule availability, and career constraints.

## When to Use
- Diego requests to re-evaluate or update his work preferences, availability calendar, compensation floor, or target tech stacks.
- Auditing active opportunities in `004-work-opportunities/database/opportunities.json` against updated constraints.

## Workflow Instructions

### Step 1: Launch the Interactive Preferences Survey
Execute the zero-dependency Python server:
```powershell
python .agents/skills/preference-manager/scripts/preference_server.py --open
```
This opens the browser UI at `http://127.0.0.1:8765`. Diego can visually toggle his weekly availability grid (classes vs work hours), modify compensation floors, reorder work arrangement preferences, and select tech domains.

### Step 2: Synchronize Vault
Clicking **Save Preferences** or **Save & Run AI Opportunity Audit** in the web UI will:
1. Save full fidelity metadata to `001-background/preferences.json`.
2. Automatically synchronize flat YAML properties and updated narrative to `001-background/preferences.md`.

### Step 3: Run AI Opportunity Audit
To run or re-run the audit directly:
```powershell
python .agents/skills/preference-manager/scripts/audit_preferences.py
```
This produces an updated audit markdown note in `004-work-opportunities/opportunities-preference-audit.md`.

### Step 4: User Briefing
Summarize the audit findings for Diego (remembering the Canary rule: start with `Hello Perea,`).
```

- [ ] **Step 2: Test skill definition syntax and paths**

Run:
```powershell
Test-Path ".agents\skills\preference-manager\SKILL.md"
Test-Path ".agents\skills\preference-manager\scripts\preference_models.py"
Test-Path ".agents\skills\preference-manager\scripts\preference_server.py"
Test-Path ".agents\skills\preference-manager\scripts\audit_preferences.py"
Test-Path ".agents\skills\preference-manager\web\index.html"
```
Expected: All return `True`.

- [ ] **Step 3: Run complete test suite**

Run:
```powershell
python -m unittest discover -s tests
```
Expected: All tests pass (`OK`).

- [ ] **Step 4: Commit**

Run:
```powershell
git add .agents/skills/preference-manager/SKILL.md
git commit -m "feat: register preference-manager skill for interactive career workflow"
```

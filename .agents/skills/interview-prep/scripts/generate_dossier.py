#!/usr/bin/env python3
"""
Generates targeted interview preparation dossiers with STAR behavioral stories,
technical question drills, and system design talking points grounded in vault evidence.
"""

from typing import Dict, List, Any, Optional
import argparse
import sys
from pathlib import Path

# Add 001-background to path to import candidate_profile
BACKGROUND_DIR = Path(__file__).resolve().parent.parent.parent.parent / "001-background"
if str(BACKGROUND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKGROUND_DIR))

try:
    import candidate_profile
except ImportError:
    candidate_profile = None


def format_star_story(title: str, situation: str, task: str, action: str, result: str) -> str:
    """Formats a structured STAR behavioral story in Markdown."""
    return f"""### {title}
- **Situation:** {situation}
- **Task:** {task}
- **Action:** {action}
- **Result:** {result}
"""


def build_dossier_markdown(
    role_info: Dict[str, Any],
    background_assets: List[Dict[str, Any]],
    candidate_name: Optional[str] = None,
) -> str:
    """Builds a complete Markdown interview dossier for an opportunity."""
    if candidate_name is None:
        if candidate_profile:
            candidate_name = candidate_profile.load_profile().get("name", "Candidate")
        else:
            candidate_name = "Candidate"

    company = role_info.get("company", "Target Company")
    role = role_info.get("role", "Target Role")
    tech_stack = ", ".join(role_info.get("tech_stack", []))

    star_sections = ""
    for asset in background_assets:
        star = asset.get("star", {})
        star_sections += format_star_story(
            title=asset.get("title", "Project"),
            situation=star.get("s", "Context"),
            task=star.get("t", "Challenge"),
            action=star.get("a", "Implementation"),
            result=star.get("r", "Measurable Impact")
        ) + "\n"

    return f"""---
created: 2026-10-02
type: interview-dossier
candidate: "{candidate_name}"
company: "{company}"
role: "{role}"
status: active
tags: [interview-prep, technical-interview, star-method]
---

# Interview Preparation Dossier: {company} — {role}

## 1. Company & Role Intelligence
- **Candidate:** {candidate_name}
- **Target Company:** {company}
- **Role:** {role}
- **Core Technologies:** {tech_stack or "General Software / AI"}

---

## 2. Behavioral STAR Grid (Grounded in Verified Background)
{star_sections}
---

## 3. Technical Question Bank & Architectural Drills
### Core Technical Competencies
- Explain trade-offs in distributed systems / high-throughput inference pipelines.
- Deep dive into concurrency, memory management, and GPU/NPU hardware acceleration.
- Describe how you handle model evaluation, hallucinations, or covariate drift.

### 5 Questions to Ask the Interviewer (Reverse Screen)
1. "What does the deployment and validation lifecycle look like for models transitioning from experimentation to production here?"
2. "What are the most challenging latency or throughput bottlenecks the team is currently untangling?"
3. "How does engineering collaborate with product when prioritizing reliability over new feature velocity?"
4. "What is the expected scope of ownership for an intern on this team during the first 6 weeks?"
5. "What distinguishes the top 5% of performers who have gone through this group?"
"""


def main():
    parser = argparse.ArgumentParser(description="Generate interview prep dossier")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--role", required=True, help="Role name")
    parser.add_argument("--stack", nargs="*", default=[], help="Tech stack keywords")
    parser.add_argument("--candidate-name", help="Candidate full name")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    role_info = {
        "company": args.company,
        "role": args.role,
        "tech_stack": args.stack,
    }
    content = build_dossier_markdown(role_info, [], candidate_name=args.candidate_name)
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Dossier written to {out_path}")
    else:
        print(content)


if __name__ == "__main__":
    main()

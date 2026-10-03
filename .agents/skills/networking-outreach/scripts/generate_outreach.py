"""Networking Outreach Generator.

Generates 3-tier cold outreach and referral templates (Alumni, Recruiter, Hiring Manager)
tailored to specific target roles and candidate accomplishments.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add 001-background to path to import candidate_profile
BACKGROUND_DIR = Path(__file__).resolve().parent.parent.parent.parent / "001-background"
if str(BACKGROUND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKGROUND_DIR))

try:
    import candidate_profile
except ImportError:
    candidate_profile = None


def get_default_candidate_info() -> Dict[str, Any]:
    """Retrieve default candidate profile info from candidate_profile or preferences.json."""
    if candidate_profile:
        try:
            prof = candidate_profile.load_profile()
            return {
                "name": prof.get("name", "Candidate"),
                "school": prof.get("school", "University"),
                "highlight": "delivered high-throughput distributed systems & ML pipelines",
            }
        except Exception:
            pass

    pref_path = BACKGROUND_DIR / "preferences.json"
    if pref_path.exists():
        try:
            with open(pref_path, "r", encoding="utf-8") as f:
                pref_data = json.load(f)
                cand = pref_data.get("candidate", {})
                return {
                    "name": cand.get("name", "Candidate"),
                    "school": cand.get("university", "University"),
                    "highlight": "delivered high-throughput distributed systems & ML pipelines",
                }
        except Exception:
            pass

    return {
        "name": "Candidate",
        "school": "University",
        "highlight": "delivered high-throughput distributed systems & ML pipelines",
    }


def build_outreach_templates(
    role_info: Dict[str, Any],
    candidate_info: Optional[Dict[str, Any]] = None,
    alumni_name: Optional[str] = None,
    recruiter_name: Optional[str] = None,
    hm_name: Optional[str] = None,
) -> Dict[str, str]:
    """Build 3-tier networking templates (alumni, recruiter, hiring manager).

    Args:
        role_info: Dictionary containing 'company', 'role', and 'key_skill'.
        candidate_info: Dictionary containing 'name', 'school', and 'highlight'.
        alumni_name: Optional specific name for the alumni contact.
        recruiter_name: Optional specific name for the recruiter contact.
        hm_name: Optional specific name for the hiring manager contact.

    Returns:
        Dictionary with keys 'alumni', 'recruiter', and 'hiring_manager'.
    """
    if not candidate_info:
        if candidate_profile:
            prof = candidate_profile.load_profile()
            candidate_info = {
                "name": prof.get("name", "Candidate"),
                "school": prof.get("school", "University"),
                "highlight": "delivered high-throughput distributed systems & ML pipelines",
            }
        else:
            candidate_info = {
                "name": "Candidate",
                "school": "University",
                "highlight": "delivered high-throughput distributed systems & ML pipelines",
            }

    company = role_info.get("company", "[Company]")
    role = role_info.get("role", "[Role]")
    key_skill = role_info.get("key_skill", "Distributed Systems & Machine Learning")

    cand_name = candidate_info.get("name", "Candidate")
    cand_school = candidate_info.get("school", "University")
    cand_highlight = candidate_info.get(
        "highlight", "delivered high-throughput distributed systems & ML pipelines"
    )

    alumni_salutation = f"Hi {alumni_name}," if alumni_name else "Hi [Alumni Name],"
    recruiter_salutation = f"Hi {recruiter_name}," if recruiter_name else "Hi [Recruiter Name],"
    hm_salutation = f"Dear {hm_name}," if hm_name else "Dear [Hiring Manager Name],"

    # Tier 1: Alumni Outreach (Shared alma mater, warm connection, seeking culture/work insights)
    alumni_template = f"""{alumni_salutation}

I noticed you're working at {company} and that we both attended {cand_school}! I am currently studying Computer Science and Technology at {cand_school} and preparing to apply for the {role} role at {company}.

I have been working extensively with {key_skill}—most recently, I {cand_highlight}. I'm really impressed by the engineering challenges your team is solving at {company}.

If you have 10-15 minutes in the coming weeks, I would love to learn more about your journey from {cand_school} to {company} and what you enjoy most about the engineering culture. No worries if you're busy!

Best regards,
{cand_name}"""

    # Tier 2: Recruiter Outreach (Direct, professional, value proposition, timeline inquiry)
    recruiter_template = f"""{recruiter_salutation}

I hope you're having a great week. I recently applied for the {role} position at {company} and wanted to reach out directly to express my enthusiasm.

I specialize in {key_skill} and bring proven hands-on experience in high-performance engineering. For instance, I recently {cand_highlight}, demonstrating strong systems-level optimization and scalable architecture design.

Given {company}'s leadership in this space, I am eager to contribute to your engineering initiatives. Could you let me know if you are the recruiter leading hiring for this role, or if there is someone specific on the talent team I should connect with?

Thank you for your time and consideration!

Best regards,
{cand_name}"""

    # Tier 3: Hiring Manager Outreach (High technical depth, engineering impact, immediate value)
    hm_template = f"""{hm_salutation}

I've been following your engineering team's advancements at {company} and wanted to reach out regarding the {role} opening.

My background centers on {key_skill}. In my latest technical project, I {cand_highlight}. I focus heavily on writing production-ready, highly optimized code and tackling complex distributed workflows.

I would welcome the opportunity to discuss how my technical background and hands-on systems experience can support your team's upcoming milestones at {company}. Would you be open to a brief 10-minute technical chat sometime next week?

Best regards,
{cand_name}"""

    return {
        "alumni": alumni_template.strip(),
        "recruiter": recruiter_template.strip(),
        "hiring_manager": hm_template.strip(),
    }


def format_outreach_markdown(
    role_info: Dict[str, Any],
    candidate_info: Optional[Dict[str, Any]] = None,
    alumni_name: Optional[str] = None,
    recruiter_name: Optional[str] = None,
    hm_name: Optional[str] = None,
) -> str:
    """Format outreach templates into a structured Markdown document."""
    if not candidate_info:
        candidate_info = get_default_candidate_info()

    company = role_info.get("company", "[Company]")
    role = role_info.get("role", "[Role]")
    templates = build_outreach_templates(
        role_info,
        candidate_info,
        alumni_name=alumni_name,
        recruiter_name=recruiter_name,
        hm_name=hm_name,
    )

    md = f"""# Networking Outreach: {company} - {role}

**Company**: {company}
**Target Role**: {role}
**Key Skill**: {role_info.get('key_skill', 'N/A')}
**Candidate Highlight**: {candidate_info.get('highlight', 'N/A')}

---

### Tier 1: Alumni Outreach
*Target*: Alumni from {candidate_info.get('school') or candidate_info.get('university', 'University')} at {company}.
*Goal*: Build rapport, ask about team culture, request advice or internal referral.

```markdown
{templates['alumni']}
```

---

### Tier 2: Recruiter Outreach
*Target*: Technical / University Recruiters hiring for {role}.
*Goal*: Confirm application status, highlight core competency, request screener interview.

```markdown
{templates['recruiter']}
```

---

### Tier 3: Hiring Manager Outreach
*Target*: Engineering Managers / Tech Leads managing the team for {role}.
*Goal*: Demonstrate domain mastery, technical impact, and propose high-value contribution.

```markdown
{templates['hiring_manager']}
```
"""
    return md.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate 3-tier networking and referral outreach templates."
    )
    parser.add_argument("--company", required=True, help="Target company name")
    parser.add_argument("--role", required=True, help="Target role title")
    parser.add_argument("--key-skill", default="Distributed Systems & ML", help="Target skill")
    parser.add_argument(
        "--candidate-name", default=None, help="Candidate full name"
    )
    parser.add_argument(
        "--school", default=None, help="Candidate alma mater"
    )
    parser.add_argument(
        "--highlight",
        default=None,
        help="Top technical achievement or metric",
    )
    parser.add_argument("--alumni-name", help="Specific alumni name")
    parser.add_argument("--recruiter-name", help="Specific recruiter name")
    parser.add_argument("--hm-name", help="Specific hiring manager name")
    parser.add_argument("--output", help="Optional path to output markdown file")
    parser.add_argument(
        "--json", action="store_true", help="Output templates in JSON format"
    )

    args = parser.parse_args()

    role_info = {
        "company": args.company,
        "role": args.role,
        "key_skill": args.key_skill,
    }
    candidate_info = None
    if args.candidate_name or args.school or args.highlight:
        default_info = get_default_candidate_info()
        candidate_info = {
            "name": args.candidate_name or default_info.get("name", "Candidate"),
            "school": args.school or default_info.get("school", "University"),
            "highlight": args.highlight
            or default_info.get(
                "highlight",
                "delivered high-throughput distributed systems & ML pipelines",
            ),
        }

    if args.json:
        templates = build_outreach_templates(
            role_info,
            candidate_info,
            alumni_name=args.alumni_name,
            recruiter_name=args.recruiter_name,
            hm_name=args.hm_name,
        )
        content = json.dumps(templates, indent=2)
    else:
        content = format_outreach_markdown(
            role_info,
            candidate_info,
            alumni_name=args.alumni_name,
            recruiter_name=args.recruiter_name,
            hm_name=args.hm_name,
        )

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Outreach templates successfully written to {args.output}")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    sys.exit(main())

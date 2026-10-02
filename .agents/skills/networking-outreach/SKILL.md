---
name: networking-outreach
description: Generate targeted 3-tier cold outreach, referral requests, and networking messages for alumni, recruiters, and hiring managers tailored to target roles.
---

# networking-outreach

Generates tailored, high-conversion cold outreach and referral messages across three distinct tiers (Alumni, Recruiter, Hiring Manager) for opportunities in the Career Vault.

---

## When to Use

- When applying to target companies and seeking internal referrals or informational interviews.
- When cold emailing or messaging on LinkedIn / GitHub / Email.
- When engaging with:
  1. **Alumni**: Shared university connection, warm networking, and culture insights.
  2. **Recruiters**: Campus, technical, or executive recruiters to highlight candidacy and ask about screening timelines.
  3. **Hiring Managers**: Engineering managers and tech leads to showcase deep technical alignment and high-impact metrics (e.g., high-throughput systems, latency optimizations).

---

## The 3-Tier Strategy

### 1. Tier 1: Alumni Outreach
- **Audience**: Alumni from candidate's university currently working at target company.
- **Tone**: Warm, conversational, respectful of time, seeking advice rather than direct job demands.
- **Goal**: Establish rapport, learn about team culture, and secure internal referrals organically.
- **Call-to-Action**: Low-friction 10-15 minute coffee chat or advice exchange.

### 2. Tier 2: Recruiter Outreach
- **Audience**: Technical and University Recruiters managing applications for the target role.
- **Tone**: Professional, crisp, concise, value-oriented.
- **Goal**: Confirm application submission, highlight match with core competencies, and bypass ATS filtering.
- **Call-to-Action**: Clarify recruiting timeline or schedule a quick screening call.

### 3. Tier 3: Hiring Manager Outreach
- **Audience**: Engineering Leads, Directors, and Tech Managers overseeing the specific project/team.
- **Tone**: Technically rigorous, impact-driven, highlighting concrete systems achievements.
- **Goal**: Demonstrate how candidate directly solves team problems and adds value from Day 1.
- **Call-to-Action**: Brief 10-15 minute technical discussion on the team's engineering roadmap.

---

## CLI & Script Usage

The helper script [`generate_outreach.py`](.agents/skills/networking-outreach/scripts/generate_outreach.py) automates template generation:

```bash
# Basic generation to stdout
py -3.11 .agents/skills/networking-outreach/scripts/generate_outreach.py \
  --company "Databricks" \
  --role "Data Systems Intern" \
  --key-skill "Lakehouse & Spark Optimization" \
  --highlight "Achieved 3,700 FPS distributed RL training pipeline"

# Save directly to a markdown note in 004-work-opportunities/
py -3.11 .agents/skills/networking-outreach/scripts/generate_outreach.py \
  --company "Databricks" \
  --role "Data Systems Intern" \
  --key-skill "Lakehouse & Spark Optimization" \
  --output "004-work-opportunities/2026-10-databricks-outreach.md"

# Output as structured JSON
py -3.11 .agents/skills/networking-outreach/scripts/generate_outreach.py \
  --company "Tesla" \
  --role "Autopilot Software Intern" \
  --json
```

---

## Vault Guidelines & Invariants

- **Ground Truth Grounding**: Never invent experiences, metrics, or credentials. Pull all candidate highlights directly from `001-background/`.
- **Obsidian Compatibility**: When saving notes to `004-work-opportunities/`, ensure flat YAML properties and alphanumeric tags (e.g., `summer-2027`, `networking`).
- **Follow-up Protocol**: Log outreach dates and responses directly in application tracker notes to track follow-up intervals (5-7 business days).

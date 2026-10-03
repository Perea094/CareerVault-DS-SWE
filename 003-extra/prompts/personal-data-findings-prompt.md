# Personal Data & Background Extraction Prompt

> **Purpose**: Standalone prompt to run in external AI chats (ChatGPT, Claude, Gemini, Copilot, or local LLMs) to extract conversation memories, personal preferences, and verified technical context for ingestion into the Career Vault.
> **Destination**: Output files must be saved to `001-background/findings/{AI name}-findings-{date YYYY-MM-DD}.md`.

---

## The Extraction Prompt (Copy & Paste to External AI):

```markdown
Review our entire conversation history, saved custom instructions, and any persistent memories about me. Generate a comprehensive personal background and preference file named `{AI name}-findings-{date YYYY-MM-DD}.md`.

Format the output strictly with Obsidian-compatible flat YAML frontmatter at the top:
---
created: {YYYY-MM-DD}
updated: {YYYY-MM-DD}
type: findings
source: {AI Name or Model}
tags:
  - findings
  - candidate-profile
  - background
---

Organize the findings into the following structured sections using clear bullet points. If any category has no data in our history, explicitly write "No recorded findings" rather than omitting it. Be factual, objective, and cite specific projects, messages, or decisions where possible.

### 1. Personal & Professional Identity
- Full name and contact details (if shared)
- Current geographic location and university/institutional affiliation
- Primary professional identity and target job titles (e.g., Data Science, Machine Learning Engineering, SWE)

### 2. Work Authorization & Geographic Constraints
- Current work authorization, citizenship, or visa sponsorship requirements
- Target geographic regions and relocation willingness
- Work modality preferences (Remote, Hybrid, Onsite ranking)

### 3. Technical Stack & Domain Depth
- Core programming languages and declared proficiency
- Machine learning, deep learning, and data science frameworks
- Software engineering, cloud, databases, and DevOps/MLOps tooling
- Key technical domains of interest (e.g., LLMs, Computer Vision, RL, Systems) and excluded domains

### 4. Availability & Working Modality
- Target weekly working hours (e.g., 20-30 hrs/week part-time vs 40 hrs/week full-time)
- Weekly class schedule or recurring time commitments
- Preferred communication cadence (async vs sync)

### 5. Compensation & Benefits Priorities
- Minimum acceptable hourly or annual compensation floor
- Priority benefits (health insurance, learning budget, hardware stipend, 401k)

### 6. Active Projects & Proven Achievements
- Notable technical projects, repositories, hackathons, or research initiatives mentioned
- Concrete quantifiable metrics or results discussed (Google XYZ format: accomplished X, measured by Y, by doing Z)

### 7. Communication Style & Working Preferences
- Preferred response tone (concise, direct, academic, bulleted, etc.)
- Formatting habits and presentation preferences

### 8. Feedback, Corrections & Anti-Patterns
- Explicit feedback or corrections I have provided in past interactions
- Dealbreakers, toxic workplace signals to avoid, or things I have emphasized
```

---

## Downstream Vault Ingestion Protocol (For AI Agents):

When an AI agent (Claude, OpenAI, Antigravity, or Local LLMs) ingests the resulting findings file:

1. **Save to Ground Truth**:
   - Ensure the markdown file is stored inside `001-background/findings/{AI name}-findings-{date YYYY-MM-DD}.md`.

2. **Cross-Check with `001-background/preferences.json`**:
   - Compare extracted preferences (location, visa status, hourly floor, target hours, excluded industries) against `001-background/preferences.json`.
   - Update `001-background/preferences.json` and sync `001-background/preferences.md` with newly discovered verified constraints.

3. **Cross-Check Technical Experience**:
   - If new projects or quantified accomplishments are identified, flag them for ingestion into `001-background/projects/` or `001-background/experiences/` using the vault blueprint format (`001-background/templates/project-blueprint.md`).

4. **Strict Grounding Rule**:
   - Never extrapolate or invent details beyond what the external AI documented. If an entry is ambiguous, mark it as pending user confirmation.


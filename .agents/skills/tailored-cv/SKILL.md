---
name: tailored-cv
description: Use when adapting the candidate's CV for a specific job posting, internship application, or clustering multiple opportunities into archetype resumes.
---

# tailored-cv

Adapts the master CV template (`002-cv/template.tex`) and verified background assets (`001-background/`) into targeted, ATS-optimized 1-page resumes for specific roles or clustered opportunity archetypes.

---

## When to Use

- **1-to-1 Tailoring**: High-priority or specialized applications.
- **Archetype Clustering**: Batches of opportunities (3+ roles) sharing similar technical requirements.
- Translating approved Markdown CV drafts into compilation-ready LaTeX (`002-cv/Custom/*.tex`).

**Do NOT use for**: Ingesting raw experiences (use [add-experience-curriculum](.agents/skills/add-experience-curriculum/SKILL.md)), scraping job feeds (use [opportunity-scout](.agents/skills/opportunity-scout/SKILL.md)), or inventing unevidenced skills.

---

## Execution Modes

### Mode 1: 1-to-1 Dedicated CV (Single Role)

1. **Deconstruct JD**: Extract core languages, frameworks, domain requirements, and constraints from [001-background/preferences.md](001-background/preferences.md).
2. **Relevance Selection**: Prioritize the top 3 projects from [001-background/](001-background/) matching the domain:
   - *Edge AI / Vision / Robotics*: Computer vision models, embedded inference, real-time pipelines.
   - *RL / Systems / Performance*: Deep reinforcement learning agents, distributed architectures.
   - *Data / Lakehouse / SQL*: Distributed pipelines, ETL/ELT, Lakehouse architectures.
   - *GenAI / Agents / LLMs*: Fine-tuning, RAG, tool calling, agent workflows.
3. **Draft Markdown (`002-cv/Custom/YYYY-MM-DD-<company>-<role>.md`)**:
   - Apply Google XYZ format (*Accomplished [X], measured by [Y], by doing [Z]*).
   - Reorder `Technical Skills` and `Coursework` to prioritize the JD's keywords.
   - Enforce strict 1-page density (max 3 experiences, 3 projects).
4. **LaTeX Compilation (Final Move)**: When approved, compile into `002-cv/Custom/YYYY-MM-DD-<company>-<role>.tex` using `002-cv/template.tex`.

### Mode 2: Clustered Archetype CVs (Batch Roles)

1. **Stack Intersection**: Group input opportunities into core technical archetypes:
   - **Edge AI & Vision**: C++, Linux/RTOS, Edge NPUs, OpenCV.
   - **AI & Agentic Systems**: Python, RAG, LLM fine-tuning, APIs.
   - **Data Platform & Analytics**: Distributed SQL, dbt, PySpark, Lakehouse pipelines.
   - **RL & Systems Research**: PyTorch, distributed systems, stochastic optimization, C++.
2. **Generate Archetype CV**: Create `002-cv/Custom/YYYY-MM-DD-archetype-<name>.md` for each active cluster.
3. **Distribution Matrix**: Output a concise markdown table mapping each job opening to its corresponding tailored CV file.

---

## Frontmatter & Obsidian Invariants

All Markdown CV drafts in `002-cv/Custom/` must use flat properties and alphanumeric tags:

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: custom-cv
mode: single-role # or "archetype"
target: "Company - Role" # or "Archetype Name"
status: draft # or "approved", "applied"
tags: [cv, custom-cv, summer-2027, <slug>] # Alphanumeric only: NEVER pure numbers like 2027
candidate: "Candidate Name"
candidate_profile_ref: "001-background/preferences.md"
---
```

---

## Strict Guardrails

- **Factual Ground Truth**: Every metric, tool, and claim MUST originate from [001-background/](001-background/). Zero hallucination.
- **1-Page Discipline**: Strict single-page limit in both Markdown and LaTeX.
- **Obsidian Safety**: Flat properties only (no nested YAML maps); tags must contain letters to prevent Obsidian `⚠️` warnings.

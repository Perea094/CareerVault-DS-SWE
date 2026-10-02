---
name: tailored-cv
description: Use when adapting Diego Perea León's CV for a specific job posting, internship application, or clustering multiple opportunities into archetype resumes.
---

# tailored-cv

Adapts Diego Perea León's master CV (`002-cv/general-cv.md`) and verified background assets (`001-background/`) into targeted, ATS-optimized 1-page resumes for specific roles or clustered opportunity archetypes.

---

## When to Use

- **1-to-1 Tailoring**: High-priority or specialized applications (e.g. Salesforce, Mistral, BMO, Citadel).
- **Archetype Clustering**: Batches of opportunities (3+ roles) sharing similar technical requirements.
- Translating approved Markdown CV drafts into compilation-ready LaTeX (`002-cv/Custom/*.tex`).

**Do NOT use for**: Ingesting raw experiences (use [`add-experience-curriculum`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/add-experience-curriculum/SKILL.md)), scraping job feeds (use [`opportunity-scout`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/opportunity-scout/SKILL.md)), or inventing unevidenced skills.

---

## Execution Modes

### Mode 1: 1-to-1 Dedicated CV (Single Role)

1. **Deconstruct JD**: Extract core languages, frameworks, domain requirements, and constraints from [`001-background/preferences.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.md).
2. **Relevance Selection**: Prioritize the top 3 projects from [`001-background/`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/) matching the domain:
   - *Edge AI / Vision / Robotics*: **DAVE** (Hailo-8 NPU, Raspberry Pi 5, MediaPipe, ~30 FPS).
   - *RL / Systems / Quant / C++*: **Street Fighter II RL Agent** (Ape-X DQN, QR-DQN, 3,700 FPS).
   - *Data / Lakehouse / SQL*: **Databricks Challenge** & **Aristor Consultoría** (INEGI geospatial).
   - *GenAI / Agents / LLMs*: **Local LLMs & GenAI** (Qwen/Gemma quantization, LoRA, RAG).
3. **Draft Markdown (`002-cv/Custom/YYYY-MM-DD-<company>-<role>.md`)**:
   - Apply Google XYZ format (*Accomplished [X], measured by [Y], by doing [Z]*).
   - Reorder `Technical Skills` and `Coursework` to prioritize the JD's keywords.
   - Enforce strict 1-page density (max 3 experiences, 3 projects).
4. **LaTeX Compilation (Final Move)**: When approved, compile into `002-cv/Custom/YYYY-MM-DD-<company>-<role>.tex` using [`002-cv/Diego_Perea_Resume.tex`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/002-cv/Diego_Perea_Resume.tex).

### Mode 2: Clustered Archetype CVs (Batch Roles)

1. **Stack Intersection**: Group input opportunities into 4 core technical archetypes:
   - **Edge AI & Vision**: C++, Linux/RTOS, Hailo-8 NPU, OpenCV, MediaPipe.
   - **AI & Agentic Systems**: Python, RAG, LangChain, LLM fine-tuning, APIs.
   - **Data Platform & Analytics**: Databricks, SQL, dbt, PySpark, Lakehouse pipelines.
   - **RL & Quant Research**: PyTorch, distributed systems, stochastic optimization, C++.
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
candidate: "Diego Perea León"
candidate_profile_ref: "001-background/preferences.md"
---
```

---

## Strict Guardrails

- **Factual Ground Truth**: Every metric, tool, and claim MUST originate from [`001-background/`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/). Zero hallucination.
- **1-Page Discipline**: Strict single-page limit in both Markdown and LaTeX.
- **Obsidian Safety**: Flat properties only (no nested YAML maps); tags must contain letters to prevent Obsidian `⚠️` warnings.

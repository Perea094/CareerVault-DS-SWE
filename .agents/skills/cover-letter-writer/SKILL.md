---
name: cover-letter-writer
description: Use when generating targeted, grounded cover letters or supplemental application essays tailored to specific job opportunities while strictly relying on Diego Perea León's verified background in 001-background/.
---

# cover-letter-writer

Generates targeted, compelling, and strictly grounded supplemental cover letters or application essays for specific job opportunities. Every claim, metric, and skill is anchored in Diego Perea León's ground-truth records in [`001-background/`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/) and aligned with [`001-background/preferences.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.md).

---

## When to Use

- **High-Priority Applications**: Writing personalized cover letters for roles where a supplemental statement is required or strongly recommended (e.g., tier-1 tech firms, cutting-edge AI research labs, startups, competitive internships).
- **Application Essay Prompts**: Drafting concise, evidence-based answers to prompts like *"Why this company?"*, *"Describe a relevant technical project"*, or *"What unique value do you bring?"*.
- **Pairing with Custom CVs**: Producing companion cover letters alongside tailored CV drafts generated in `002-cv/Custom/`.

### When NOT to Use

- Standard applications where cover letters are not accepted, ignored, or discouraged.
- Ingesting or documenting raw experiences (use [`add-experience-curriculum`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/add-experience-curriculum/SKILL.md)).
- Tailoring the resume or CV itself (use [`tailored-cv`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/.agents/skills/tailored-cv/SKILL.md)).
- Fabricating credentials, unverified enthusiasm, or ungrounded claims.

---

## Core Rules & Invariants

1. **Zero Hallucination / Strict Grounding**:
   - Every metric, framework, project, or role mentioned MUST exist in [`001-background/`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/).
   - Never invent or exaggerate past impact, revenue figures, speedups, or tools.
2. **Conciseness & High Signal**:
   - Total length should strictly be **250–350 words** (never exceeding 400 words).
   - Eliminate fluff, generic clichés (*"I am writing to express my eager interest..."*), and sycophantic corporate flattery.
3. **The 3-Paragraph Formula**:
   - **Paragraph 1: Hook & Value Alignment** (~60–80 words)
     - State the target role and immediate domain intersection without boilerplate openings.
     - Connect Diego's core engineering focus (e.g., low-latency edge AI, distributed reinforcement learning, scalable lakehouse architectures) directly to a concrete engineering challenge, team mission, or product system at the company.
   - **Paragraph 2: Deep Technical Proof (Google XYZ Formula)** (~140–180 words)
     - Highlight 1–2 verified projects or experiences from `001-background/` that directly solve or mirror the core technical requirements of the job description.
     - Formulate achievements strictly using Google's XYZ formula: *Accomplished [X], measured by [Y], by doing [Z]*.
     - Provide tangible technical context (e.g., Hailo-8 NPU hardware acceleration, Ape-X distributed DQN at 3,700 FPS, PySpark data pipelines, quantized local LLMs).
   - **Paragraph 3: Forward Look & Logistics** (~50–70 words)
     - Address operational logistics accurately based on [`001-background/preferences.md`](file:///c:/Users/Diego%20Perea/Desktop/Curriculum/001-background/preferences.md): availability window (e.g., Summer 2027), work modality preference (remote / relocation), and visa/work authorization status (Mexican citizen, open to international relocation if visa sponsored).
     - Provide a direct call to action (discussion of team challenges, live code demos, or repository walkthroughs).

---

## Output Target & Frontmatter Specification

Every cover letter draft must be written to:
`002-cv/Custom/YYYY-MM-DD-<company>-cover-letter.md`

### Obsidian-Compliant YAML Frontmatter

Obsidian requires flat properties and alphanumeric tags (never purely numerical tags like `2027`):

```yaml
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: cover-letter
company: "Target Company"
role: "Role Title"
target_opportunity: "004-work-opportunities/YYYY-MM-DD-company-role.md"
status: draft # or approved, sent
tags: [cover-letter, supplemental, summer-2027, company-slug]
candidate: "Diego Perea León"
candidate_profile_ref: "001-background/preferences.md"
---
```

---

## Step-by-Step Execution Workflow

1. **Deconstruct the Job Description (JD)**:
   - Identify core tech stack keywords (e.g., C++, PyTorch, Hailo, Databricks, Distributed Systems).
   - Identify the team's operational bottleneck or mission (e.g., real-time inference latency, training stability, pipeline throughput).
2. **Retrieve Verified Background Assets**:
   - Review relevant projects in `001-background/projects/` and experiences in `001-background/experiences/`.
   - Verify specific metrics and technologies in the corresponding markdown files.
3. **Check Constraints in `preferences.md`**:
   - Confirm role fits hard constraints and check location/sponsorship notes before drafting logistical details.
4. **Draft the Cover Letter**:
   - Follow the 3-paragraph formula with zero filler.
   - Format cleanly in Markdown with appropriate recipient header, date, and closing signature.
5. **Audit & Review**:
   - Audit against zero-hallucination rule: verify every tool and metric exists in `001-background/`.
   - Verify word count is under 400 words.
   - Check frontmatter for Obsidian property compatibility.

---

## Cover Letter Template Structure

```markdown
---
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: cover-letter
company: "Acme Corp"
role: "Machine Learning Engineer Intern"
target_opportunity: "004-work-opportunities/2026-10-15-acme-mle-intern.md"
status: draft
tags: [cover-letter, supplemental, summer-2027, acme]
candidate: "Diego Perea León"
candidate_profile_ref: "001-background/preferences.md"
---

# Application: Machine Learning Engineer Intern — Acme Corp

**Diego Perea León**  
Querétaro, Mexico · [GitHub](https://github.com/DiegoPerea20) · [LinkedIn](https://linkedin.com/in/diego-perea-leon) · [Email](mailto:diego.perea@example.com)  
*Date: YYYY-MM-DD*

---

Dear [Hiring Team / Engineering Lead at Acme Corp],

[Paragraph 1: Hook & Value Alignment — Direct statement of role, immediate connection between Diego's systems/ML focus and Acme's technical problem without boilerplate openings.]

[Paragraph 2: Deep Technical Proof — Google XYZ breakdown of 1–2 verified projects from 001-background/, detailing concrete architectural decisions, frameworks, and quantifiable performance metrics.]

[Paragraph 3: Forward Look & Logistics — Stated availability window, work modality / visa sponsorship alignment from preferences.md, and proactive call to action for technical conversation.]

Sincerely,  
**Diego Perea León**
```

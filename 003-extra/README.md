# 003-extra — Prompts & Agent Systems Layer

## 1. Overview
The `003-extra/` directory serves as the centralized prompt engineering, evaluation rubric, and auxiliary agent tooling layer for the Career Vault.

While `.agents/skills/` contains the execution engines for native Antigravity workflows, `003-extra/` provides universal, self-contained prompt templates and system instructions designed to be executed across **any AI agent environment**, including:
- **Google Antigravity (AGY)**
- **Anthropic Claude** (Claude Code, Claude 3.5 Sonnet, Claude Opus)
- **OpenAI Models** (ChatGPT, GPT-4o, Assistants API)
- **Local LLMs** (DeepSeek, Llama-3, Mistral, Qwen via Ollama, LM Studio, or vLLM)
- **CLI Automation & Schedulers** (PowerShell, bash, cron, GitHub Actions)

---

## 2. Core Architectural Principles

### Dynamic Source of Truth (No Hardcoded Assumptions)
- **Zero Hardcoded Candidate Details**: Prompts and rubrics in this directory must **never** hardcode candidate names, geographic locations, citizenship/visa status, university graduation years, or hourly pay rates.
- **Dynamic Inspection**: All prompts instruct agents to dynamically inspect:
  1. `001-background/preferences.json` (canonical machine configuration for constraints, hours, and pay floors).
  2. `001-background/preferences.md` (human-readable view of preferences).
  3. `001-background/` subdirectories (`experiences/`, `projects/`, `education/`, `findings/`) for verified background truth.

### Universal Cross-Agent Consumability
Every prompt template in `003-extra/prompts/` follows an elastic format:
1. **Clear Role & Mission**: Explicit recruiter/evaluator persona with strict bar-raiser standards.
2. **Explicit Input Paths**: Direct file paths relative to the vault root so any agent runtime can locate them.
3. **Reproducible Step-by-Step Instructions**: Unambiguous, deterministic steps with fallback modes for agents without terminal or skill execution tools.
4. **Obsidian Property Compliance**: All generated notes enforce flat YAML frontmatter (`created`, `updated`, `type`, `tags`) and non-numerical tags (e.g., `summer-2027`, never pure numbers).

---

## 3. Directory Layout

```
003-extra/
├── README.md                                  # Layer documentation & cross-agent guidelines
└── prompts/
    ├── daily-opportunities-audit-prompt.md    # Multi-agent prompt for scheduled daily scout & triage
    ├── personal-data-findings-prompt.md       # Memory & preference extraction prompt for external AIs
    ├── opportunity-triage-rubric-prompt.md    # Universal role evaluation rubric & screening prompt
    └── expert-recruiter-cv-audit-prompt.md    # Comprehensive CV audit & 5-pillar scoring prompt
```

---

## 4. Prompt Catalog & Usage

### 1. `daily-opportunities-audit-prompt.md`
- **Use Case**: Automated daily check for new tech opportunities, pipeline database updates, and executive briefing.
- **Runners**: Supports Antigravity `/schedule`, cron jobs, Claude Code, and OpenAI batch runners.
- **Engine**: Triggers `004-work-opportunities/scripts/scan_opportunities.py` and syncs `004-work-opportunities/database/opportunities.json`.

### 2. `personal-data-findings-prompt.md`
- **Use Case**: Run inside external AI chats to extract personal preferences, work constraints, and technical context from historical chats.
- **Output Destination**: `001-background/findings/{AI name}-findings-{date YYYY-MM-DD}.md`.
- **Downstream Ingestion**: AI agents parse the note to update `001-background/preferences.json`.

### 3. `opportunity-triage-rubric-prompt.md`
- **Use Case**: Evaluating an individual job posting against candidate dealbreakers, location requirements, and compensation floors.
- **Output**: Generates structured evaluation notes in `004-work-opportunities/<company>/`.

### 4. `expert-recruiter-cv-audit-prompt.md`
- **Use Case**: Auditing a master CV or tailored draft with 10+ year technical recruiter rigor.
- **Methodology**: 5 assessment pillars (Impact & Google XYZ, Technical Depth, Signal-to-Noise, ATS Parseability, Leadership) with 0–100 scoring.

# Daily Opportunity Scout Scheduler Prompt

> **Purpose**: Minimalist, 1-line system prompt for automated daily schedulers and cron tasks.
> **Skill Engine**: Powered by the vault skill [`opportunity-scout`](.agents/skills/opportunity-scout/SKILL.md).

---

### Daily Scheduler Prompt (Copy & Paste for `/schedule` or Cron):

```text
Execute the opportunity-scout skill workflow to check for newly posted tech opportunities, update the database and monthly audit note, and provide a brief summary of top matches.
```

---

### What this triggers behind the scenes:
1. Ingests and deduplicates tech opportunity feeds via `004-work-opportunities/scripts/scan_opportunities.py`.
2. Evaluates viable roles using the `expert-recruiter` methodology against `001-background/preferences.md`.
3. Appends new roles to `004-work-opportunities/database/opportunities.json` and syncs `opportunities.csv`.
4. Updates the monthly Markdown note: `004-work-opportunities/opportunities-audit-YYYY-MM.md`.
5. Delivers a 3-bullet executive briefing highlighting top viable opportunities.

---
name: application-tracker
description: Track and update job application lifecycle stages (wishlist, applied, oa_received, screening, interview, offer, rejected, withdrawn) across 004-work-opportunities/ and generate Obsidian Kanban pipeline boards.
---

# application-tracker

Maintains status tracking across active job submissions, logging application dates, custom CV versions used, and recruiter communication.

## When to Use
- When applying to a job posting in `004-work-opportunities/`.
- When receiving an Online Assessment (OA), interview invitation, or decision.
- Generating or updating the master `004-work-opportunities/application-pipeline.md` dashboard.

## Application Lifecycle Stages
1. `wishlist` — Identified opportunities not yet applied to.
2. `applied` — Application submitted with tailored CV.
3. `oa_received` — HackerRank / Codesignal / technical test sent.
4. `screening` — Recruiter screening interview scheduled.
5. `interview` — Technical / hiring manager interviews in progress.
6. `offer` — Job offer received.
7. `rejected` — Rejection recorded.
8. `withdrawn` — Application voluntarily withdrawn.

## Target Paths
- **Database:** `004-work-opportunities/database/opportunities.json`
- **Dashboard Note:** `004-work-opportunities/application-pipeline.md`
- **Engine Script:** `.agents/skills/application-tracker/scripts/track_application.py`

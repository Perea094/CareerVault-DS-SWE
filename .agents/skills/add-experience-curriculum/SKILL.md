---
name: add-experience-curriculum
description: Use when adding, ingesting, or documenting a professional experience, project, startup, internship, or university challenge (from a GitHub/local repo, narrative, or notes) into the career vault.
---

# add-experience-curriculum

Automates documenting professional experiences, industry challenges, and technical projects into the central career vault (`Career Vault`) from any project or workspace globally.

## Target Vault Paths
The skill operates using paths relative to the vault root (or detected workspace root):
- **Vault Root:** `.` (Career Vault workspace root)
- **Experiences Directory:** `001-background/experiences/`
- **Consolidated Findings:** `001-background/findings/consolidated-findings.md`

## Workflow

1. **Extract Evidence (Factual Ground Truth)**
   - **GitHub / Local Repo:** Inspect `README.md`, package manifests (`package.json`, `pyproject.toml`), test suites, and git commits for verified metrics, dates, and architecture.
   - **Narrative / Notes:** Extract role, organization, dates, problem, tech stack, and achievements.
   - **Strict Rule:** Never invent metrics, benchmarks, or tools. All claims must be grounded in evidence.

2. **Format Experience Entry**
   Apply Google XYZ formula (*Accomplished [X], measured by [Y], by doing [Z]*) strictly following `001-background/templates/experience-blueprint.md`:
   ```markdown
   ### Organization / Company — Role Title
   *Modality (Remote/Hybrid/Onsite) | Location | Month YYYY – Month YYYY*
   *Official Repo / Project URL:* [link](https://...)

   - **Context & Problem:** Institutional scale, traffic volume, or operational bottleneck being addressed.
   - **Stack & Architecture:** Languages (Python, C++, SQL), frameworks (PyTorch, FastAPI, Spark), and hardware/cloud platforms.
   - **Impact & Metrics (Google XYZ):** Accomplished [X], measured by [Y] (e.g. latency, throughput, accuracy, cost), by doing [Z].
   - **Testing & Verification:** Test coverage, benchmarks, automated validation, and peer review.
   ```

3. **Temporal Snapshot & History Preservation**
   - Find the latest `experiences-YYYY-MM-DD.md` in `001-background/experiences/`.
   - Read the existing file in full. **Never drop past history**—new snapshots are cumulative.
   - Create `experiences-YYYY-MM-DD.md` using today's date with YAML frontmatter:
     ```yaml
     ---
     created: YYYY-MM-DD
     updated: YYYY-MM-DD
     type: experience
     tags: [background, experience, industry, swe, data-science]
     status: evergreen
     ---
     ```
   - Insert new experience under the relevant universal section:
     - `## Industry Experience` (Internships, formal employment, contracted roles)
     - `## Technical Projects & Challenges` (Industry challenges, open source systems)
     - `## Startups & Leadership` (Venture leadership, founding roles)
     - `## Student Organizations & Competitions` (Engineering clubs, hackathons, contests)
     - `## Academic Research & Publications` (Research labs, published papers, capstones)

4. **Integrity & Backlinks**
   - In superseded file, add top callout:
     `> [!NOTE]`
     `> This version has been superseded by [[experiences-YYYY-MM-DD|Title]].`
   - In `001-background/findings/consolidated-findings.md` (or findings audit note):
     - Update YAML `updated: YYYY-MM-DD`.
     - Append bullet summary under `## Subdirectory: experiences/`.

5. **Verify & Report**
   - Confirm file creation and links. Present brief summary with clickable `file://` links.

## Invariants
- **Vault-Relative Paths:** Never use traversal paths like `../001-background`; resolve relative to the vault root.
- **Cumulative Snapshots:** Always carry forward existing historical experiences.
- **Factual Integrity:** Reject hallucinated metrics or unverified technologies.

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
   Apply Google XYZ formula (*Accomplished [X], measured by [Y], by doing [Z]*):
   ```markdown
   ### Organization / Socio Formador — Role Title
   *Modality / Context | Location | Month YYYY – Month YYYY*
   *Repositorio Oficial:* [owner/repo](url)

   - **Contexto & Problema:** Institutional scope, scale, and operational bottleneck.
   - **Stack & Arquitectura:** Exact languages, frameworks, databases, and architectural patterns.
   - **Funcionalidades & Métricas:** Measurable impact, key features, throughput, latency, or scale.
   - **Calidad & Testing:** Automated test suites, coverage, specs, and validation results.
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
     tags: [background, experience, socio-formador, fullstack, ...]
     status: evergreen
     ---
     ```
   - Insert new experience under the relevant section:
     - `## Proyectos de Vinculación con Socios Formadores (Tecnológico de Monterrey)` (Tec21 challenges)
     - `## Experiencia en Industria` (Internships, formal employment)
     - `## Liderazgo & Startups` (Own ventures, executive roles)
     - `## Organizaciones Estudiantiles & Competiciones` (LEIA, hackathons, contests)
     - `## Investigación & Proyectos Académicos` (Research, papers)

4. **Integrity & Backlinks**
   - In superseded file, add top callout:
     `> [!NOTE]`
     `> Esta versión ha sido sucedida por [[experiences-YYYY-MM-DD|Título]].`
   - In `001-background/findings/consolidated-findings.md`:
     - Update YAML `updated: YYYY-MM-DD`.
     - Append bullet summary under `## 12. Subdirectory: experiences/`.

5. **Verify & Report**
   - Confirm file creation and links. Present brief summary with clickable `file://` links.

## Invariants
- **Vault-Relative Paths:** Never use traversal paths like `../001-background`; resolve relative to the vault root.
- **Cumulative Snapshots:** Always carry forward existing historical experiences.
- **Factual Integrity:** Reject hallucinated metrics or unverified technologies.

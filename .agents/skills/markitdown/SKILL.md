---
name: markitdown
description: Use when importing, ingesting, or converting external academic files (PDF, DOCX, PPTX, XLSX, HTML, TXT, or audio) into the Obsidian vault, routing notes to semester and course folders, and connecting concepts using Obsidian search and backlinks.
---

# MarkItDown Academic Ingestion

## Overview

Converts academic documents (lecture slides, papers, homework guides, spreadsheets) into clean Markdown notes using Microsoft's MarkItDown engine, dynamically routes them into semester and course folders, and uses Obsidian search tools to link related concepts across the vault.

## When to Use

Use this skill when:
- The user uploads or provides paths to academic documents (`.pdf`, `.pptx`, `.docx`, `.xlsx`, `.html`, `.txt`).
- Converting lecture slides or syllabi into notes for university courses.
- Integrating external reading materials while automatically discovering topic connections in the vault.
- Creating new course folders or future semester notes from external files.

When NOT to use:
- Quick manual text edits to existing notes (use `replace_file_content` instead).
- Non-document queries or tasks that do not involve converting external files.

---

## Quick Reference

| Action | Command / Tool |
| :--- | :--- |
| Convert document to JSON | `py -3.11 .agents/skills/markitdown/scripts/convert.py --input "<filepath>" --json` |
| Scan semesters & courses | `py -3.11 .agents/skills/markitdown/scripts/vault_helper.py --scan` |
| Match text to course folders | `py -3.11 .agents/skills/markitdown/scripts/vault_helper.py --match "<text>"` |
| Search vault for concept | `obsidian search:context query="<concept>" limit=5` |
| List vault tags | `obsidian tags counts` |
| Create new note | `obsidian create path="<semester>/<course>/<title>.md" content="..."` |

---

## Step-by-Step Ingestion Workflow

### Step 1: Ingest & Convert File
When a user provides a file path or uploads a file into the conversation:
1. Run the MarkItDown conversion runner:
   ```powershell
   py -3.11 .agents/skills/markitdown/scripts/convert.py --input "<filepath>" --json
   ```
2. Extract the resulting JSON object containing `title`, `filename`, `ext`, and `text`.

### Step 2: Dynamic Course & Semester Routing
1. Discover existing semesters and courses:
   ```powershell
   py -3.11 .agents/skills/markitdown/scripts/vault_helper.py --match "<first 500 characters of text>"
   ```
2. Identify the highest-scoring course.
3. If the document belongs to a new class or an upcoming semester (e.g. `006-Sexto Semestre`):
   - Propose creating the new folder structure:
     ```powershell
     py -3.11 .agents/skills/markitdown/scripts/vault_helper.py --create "<Semester>" "<Course>"
     ```

### Step 3: Vault Concept Discovery (Obsidian CLI)
Extract 3 to 5 core academic concepts, algorithms, or formulas from the converted Markdown.
For each key concept, query the vault for existing notes:
```powershell
obsidian search:context query="<key-concept>" limit=3
```
Check existing vault tags:
```powershell
obsidian tags counts
```

### Step 4: Interactive Confirmation Gate
Before writing the note into the vault, present a clear proposal to the user:
- **Suggested Destination**: `<Semester>/<Course>`
- **Note Title**: `<Extracted or proposed title>`
- **Suggested Tags**: `#concept1`, `#course`
- **Discovered Connections**: 3–5 candidate notes discovered via Obsidian search
- Prompt the user to confirm or adjust the folder and connections.

### Step 5: Generate the Linked Note
Format the note following the vault's structure:

```markdown
---
type: note
created: YYYY-MM-DD
updated: YYYY-MM-DD
course: <Course Name>
source_file: <Source File Name>
tags:
  - tag1
  - tag2
related:
  - "[[Note 1]]"
  - "[[Note 2]]"
---

# <Note Title>

<Converted Markdown content with KaTeX mathematical formulas and inline [[wikilinks]] for relevant mentions>

---

## Connections
- [[Note 1]] — <Brief description of conceptual relationship>
- [[Note 2]] — <Brief description of conceptual relationship>
```

Write the note using `obsidian create path="..." content="..."` or `write_to_file`.

---

## Common Edge Cases & Troubleshooting

- **Image-Only or Scanned PDFs**: If MarkItDown extracts very little or no text, inform the user that the PDF is a rasterized scan requiring OCR preprocessing.
- **Novel Topic with No Vault Matches**: Do not force artificial links. Note that this is a new foundational topic and propose a new tag.
- **Multiple Files Ingestion**: Run `convert.py` on each file, aggregate discovered topics, and present a single unified confirmation prompt before writing.

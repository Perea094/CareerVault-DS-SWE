---
name: obsidian-cli
description: Use when working in an Obsidian vault or markdown notes directory, when searching, reading, creating, or editing notes via the Obsidian CLI, or when querying Obsidian tags, tasks, frontmatter properties, and templates.
---

# Obsidian CLI

## Overview

The `obsidian` CLI enables direct interaction with running or installed Obsidian instances. It provides fast indexed search, task aggregation, frontmatter property manipulation, template resolution, and full runtime access via JavaScript evaluation (`obsidian eval`).

## When to Use

Use this skill when:
- Searching for keywords, concepts, or backlinks across the vault with indexed accuracy.
- Querying pending or completed tasks (`- [ ]`, `- [x]`) across all notes.
- Inspecting, counting, or querying tags (`#tag`).
- Reading or setting frontmatter properties (YAML) without manual string parsing.
- Resolving templates with date and title expansion.
- Navigating or opening notes in the user's active Obsidian app.
- Querying Obsidian's internal `app` API via `eval`.

When NOT to use:
- Editing specific lines or multi-line sections of existing notes (use `replace_file_content` instead).
- Working in workspaces or directories that are not Obsidian vaults.

## Quick Reference

| Command | Purpose | Example |
| :--- | :--- | :--- |
| `obsidian vault` | Show current vault info | `obsidian vault` |
| `obsidian vaults` | List all known vaults | `obsidian vaults verbose` |
| `obsidian search` | Fast indexed text search | `obsidian search query="simplex"` |
| `obsidian search:context` | Search with matching line snippets | `obsidian search:context query="algorithm" limit=5` |
| `obsidian tasks` | List tasks across vault | `obsidian tasks todo verbose` |
| `obsidian task` | Toggle or update task status | `obsidian task done ref="Daily/Today.md:14"` |
| `obsidian tags` | List tags with optional counts | `obsidian tags counts sort=count` |
| `obsidian tag` | Inspect specific tag usage | `obsidian tag name="pca" verbose` |
| `obsidian read` | Read note contents | `obsidian read file="Note.md"` |
| `obsidian create` | Create a new note | `obsidian create path="Folder/Note.md" content="Hello world"` |
| `obsidian append` | Append content to existing note | `obsidian append path="Note.md" content="New text"` |
| `obsidian prepend` | Prepend content to existing note | `obsidian prepend path="Note.md" content="Header"` |
| `obsidian property:read` | Read YAML frontmatter field | `obsidian property:read name="type" file="Note.md"` |
| `obsidian property:set` | Set YAML frontmatter field | `obsidian property:set name="status" value="reviewed" file="Note.md"` |
| `obsidian template:read` | Read & resolve template variables | `obsidian template:read name="Note" resolve title="Topic"` |
| `obsidian open` | Open note in Obsidian GUI | `obsidian open file="Note.md"` |
| `obsidian eval` | Execute JS in Obsidian runtime | `obsidian eval code="app.vault.getName()"` |

## Common Workflows & Examples

### 1. Searching Notes and Inspecting Context
To find relevant notes without manually grepping:
```powershell
obsidian search:context query="stochastic processes" limit=5
```

### 2. Managing Tasks Across Notes
List all open action items across the entire vault:
```powershell
obsidian tasks todo verbose
```
Mark a specific task as done:
```powershell
obsidian task done ref="005-Semester-5/003-Stochastic-Optimization/002-Simplex.md:12"
```

### 3. Frontmatter Properties
Read metadata safely:
```powershell
obsidian property:read name="type" file="005-Principal-Component-Analysis.md"
```
Add or update frontmatter metadata:
```powershell
obsidian property:set name="reviewed" value="true" type="checkbox" file="005-Principal-Component-Analysis.md"
```

### 4. Creating Notes from Templates
Resolve template variables (like `{{title}}` and `{{date}}`) and create the note:
```powershell
$content = obsidian template:read name="Note - {{title}}" resolve title="Viterbi Algorithm"
obsidian create path="005-Semester-5/001-Analysis/Viterbi-Algorithm.md" content="$content"
```

### 5. Running Obsidian API Calls (`eval`)
Access internal data or plugins:
```powershell
obsidian eval code="app.vault.getMarkdownFiles().length"
```

## Windows & PowerShell Rules

- Parameter formatting: Obsidian CLI expects `param=value` or `param="value with spaces"`. Do not use `--param value` style flags.
- Quoting in PowerShell: When passing quotes or JSON, escape properly or pass parameters as separate tokens, e.g.:
  `obsidian search query="multivariate methods"`
- Character encoding: For files with accents or special characters, PowerShell commands should maintain UTF-8 encoding.

## Common Mistakes

| Mistake | Correction |
| :--- | :--- |
| Using `--query "term"` | Use `query="term"` (Obsidian CLI uses `key=value` format). |
| Using `obsidian read` then manually rewriting whole file with regex | Use `obsidian property:set` for frontmatter, or `replace_file_content` for specific note text edits. |
| Forgetting to specify `resolve` when reading templates | Use `obsidian template:read name="..." resolve title="..."` to substitute date and title placeholders. |
| Grepping filesystem when Obsidian app is running | Prefer `obsidian search:context` which leverages Obsidian's in-memory index. |

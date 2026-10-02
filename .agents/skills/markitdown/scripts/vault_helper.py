#!/usr/bin/env python3
"""
Vault Helper for Academic Document Ingestion.
Discovers semesters and courses dynamically across the vault and assists
in topic matching.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Pattern for semester folders (e.g. 005-Quinto Semestre, 006-Sexto Semestre, Semestre 7)
SEMESTER_PATTERN = re.compile(r"^(\d{3}-)?.*(semestre|semester)", re.IGNORECASE)

def get_vault_root(start_path: Path = None) -> Path:
    if start_path is None:
        start_path = Path(__file__).resolve()
    curr = start_path if start_path.is_dir() else start_path.parent
    while curr != curr.parent:
        if (curr / ".obsidian").is_dir() or (curr / "GEMINI.md").exists():
            return curr
        curr = curr.parent
    return Path.cwd()

def scan_vault_structure(vault_root: Path) -> Dict[str, List[str]]:
    """
    Scans the vault root for semester folders and discovers courses inside.
    Returns a dict of {semester_name: [course_folder_names]}.
    """
    structure = {}
    if not vault_root.exists():
        return structure

    for entry in sorted(vault_root.iterdir()):
        if entry.is_dir() and not entry.name.startswith("."):
            if SEMESTER_PATTERN.search(entry.name):
                courses = []
                for sub in sorted(entry.iterdir()):
                    if sub.is_dir() and not sub.name.startswith("."):
                        courses.append(sub.name)
                structure[entry.name] = courses

    return structure

def normalize_tokens(text: str) -> set:
    words = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9_]{3,}\b", text.lower())
    stopwords = {
        "para", "como", "este", "esta", "estos", "estas", "pero", "entre",
        "sobre", "todo", "todos", "toda", "todas", "desde", "hasta", "hacer",
        "tener", "estar", "clase", "notas", "apunte", "tema", "with", "from",
        "that", "this", "have", "more", "then"
    }
    return {w for w in words if w not in stopwords}

def match_courses_and_topics(text: str, vault_root: Path = None) -> List[Dict[str, Any]]:
    """
    Ranks existing courses based on keyword overlap with the document text.
    """
    if vault_root is None:
        vault_root = get_vault_root()

    structure = scan_vault_structure(vault_root)
    text_tokens = normalize_tokens(text)
    results = []

    for semester, courses in structure.items():
        for course in courses:
            # Clean course name (strip initial numbers/dashes for token matching)
            clean_name = re.sub(r"^\d{3}-", "", course)
            course_tokens = normalize_tokens(clean_name)
            
            # Count token overlap
            matches = course_tokens.intersection(text_tokens)
            score = len(matches)
            
            # Boost score if course name is explicitly in text
            if clean_name.lower() in text.lower():
                score += 5

            rel_path = f"{semester}/{course}"
            results.append({
                "semester": semester,
                "course_name": course,
                "relative_path": rel_path,
                "matched_tokens": list(matches),
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def create_course_folder(semester_name: str, course_name: str, vault_root: Path = None) -> Path:
    """
    Creates a new semester and/or course folder in the vault.
    """
    if vault_root is None:
        vault_root = get_vault_root()
    target = vault_root / semester_name / course_name
    target.mkdir(parents=True, exist_ok=True)
    return target

def main():
    parser = argparse.ArgumentParser(description="Vault Academic Structure Helper")
    parser.add_argument("--scan", action="store_true", help="Scan and list all semesters and courses")
    parser.add_argument("--match", type=str, help="Rank courses matching the provided text")
    parser.add_argument("--create", nargs=2, metavar=("SEMESTER", "COURSE"), help="Create new semester/course folder")
    parser.add_argument("--vault-path", type=str, default=None, help="Optional vault root path")

    args = parser.parse_args()
    vault_root = Path(args.vault_path) if args.vault_path else get_vault_root()

    if args.scan:
        structure = scan_vault_structure(vault_root)
        print(json.dumps(structure, ensure_ascii=False, indent=2))
    elif args.match:
        matches = match_courses_and_topics(args.match, vault_root)
        print(json.dumps(matches, ensure_ascii=False, indent=2))
    elif args.create:
        target = create_course_folder(args.create[0], args.create[1], vault_root)
        print(f"Created: {target}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

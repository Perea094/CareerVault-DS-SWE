#!/usr/bin/env python3
"""
validate_ats.py - ATS Resume Parseability Scanner

Validates compiled PDF resumes, LaTeX source files, or Markdown drafts for ATS compliance,
single-page budget enforcement, standard section headers, contact information parseability,
and text density metrics.
Uses pdfplumber to extract text from PDFs or native parsers for LaTeX and Markdown.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Union, Optional

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


CORE_SECTIONS = ["education", "experience", "projects", "skills"]

ABSTRACT_PLACEHOLDER_PATTERNS = [
    re.compile(r"<<[A-Za-z0-9_]+>>"),
    re.compile(r"\[Action Verb\]", re.IGNORECASE),
    re.compile(r"\[(?:Previous\s+)?Company[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Role[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Job Title[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Key Technical Project[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Project Title[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Start Month[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[End Month[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Dates[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[City[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[tech stack\]", re.IGNORECASE),
    re.compile(r"\[quantified[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[(?:[^\]]*\b)?X%(?:[^\]]*)?\]", re.IGNORECASE),
    re.compile(r"\[Languages:[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Frameworks[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Infrastructure:[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Honors\s*/?\s*Scholarships[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Relevant Core Coursework[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Student Organization[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Academic Mentorship[^\]]*\]", re.IGNORECASE),
    re.compile(r"\[Core Tech Stack[^\]]*\]", re.IGNORECASE),
]

# Multilingual regex support for section header detection (English and Spanish)
SECTION_PATTERNS = {
    "education": re.compile(
        r"^\s*(?:\\(?:cv)?section\*?\{)?(?:[#•\-\d\.]+\s+)?(education|academic\s+background|education\s+&\s+honors|estudios|educaci[oó]n)\b",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^\s*(?:\\(?:cv)?section\*?\{)?(?:[#•\-\d\.]+\s+)?(experience|work\s+experience|professional\s+experience|employment\s+history|experiencia)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^\s*(?:\\(?:cv)?section\*?\{)?(?:[#•\-\d\.]+\s+)?(projects|technical\s+projects|academic\s+projects|key\s+projects|proyectos)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^\s*(?:\\(?:cv)?section\*?\{)?(?:[#•\-\d\.]+\s+)?(technical\s+skills|skills|skills\s+&\s+tools|technologies|tools\s+&\s+technologies|habilidades)\b",
        re.IGNORECASE,
    ),
}

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}")
GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_\-]+|\bgithub\b", re.IGNORECASE)
LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in/)?[a-zA-Z0-9_\-]+|\blinkedin\b", re.IGNORECASE)


def detect_sections(text: str) -> List[str]:
    """Detects standard resume section headers from text lines."""
    found = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped.split()) > 7:
            continue
        for section, pattern in SECTION_PATTERNS.items():
            if pattern.search(stripped):
                found.add(section)
    return [sec for sec in CORE_SECTIONS if sec in found]


def detect_contact_info(text: str) -> Dict[str, bool]:
    """Detects essential and professional contact information."""
    return {
        "email": bool(EMAIL_PATTERN.search(text)),
        "phone": bool(PHONE_PATTERN.search(text)),
        "github": bool(GITHUB_PATTERN.search(text)),
        "linkedin": bool(LINKEDIN_PATTERN.search(text)),
    }


def detect_placeholders(text: str) -> List[str]:
    """Detects abstract template placeholders and unreplaced macros in resume text."""
    matches_with_pos = []
    for pattern in ABSTRACT_PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            token = match.group(0).strip()
            if token:
                matches_with_pos.append((match.start(), token))

    matches_with_pos.sort(key=lambda x: x[0])
    seen = set()
    unique_placeholders = []
    for _, token in matches_with_pos:
        if token not in seen:
            seen.add(token)
            unique_placeholders.append(token)
    return unique_placeholders


def check_vault_background(vault_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Checks the candidate background repository (001-background) for verified
    experience, project, and education markdown records.
    """
    if vault_root is None:
        cwd = Path.cwd()
        if (cwd / "001-background").is_dir():
            vault_root = cwd
        else:
            repo_root = Path(__file__).resolve().parents[2]
            if (repo_root / "001-background").is_dir():
                vault_root = repo_root
            else:
                vault_root = cwd
    else:
        vault_root = Path(vault_root)

    bg_dir = vault_root / "001-background"

    def count_md_files(subdir_name: str) -> int:
        subdir = bg_dir / subdir_name
        if not subdir.is_dir():
            return 0
        return sum(
            1 for p in subdir.rglob("*.md")
            if p.is_file() and p.name != ".gitkeep" and not p.name.startswith(".")
        )

    exp_count = count_md_files("experiences")
    proj_count = count_md_files("projects")
    edu_count = count_md_files("education")
    is_empty = (exp_count == 0 and proj_count == 0)

    return {
        "experiences_count": exp_count,
        "projects_count": proj_count,
        "education_count": edu_count,
        "experiences": exp_count,
        "projects": proj_count,
        "education": edu_count,
        "is_background_empty": is_empty,
    }


def calculate_ats_score(is_single_page: bool, sections_found: List[str], has_contact_info: Dict[str, bool]) -> int:
    """
    Calculates ATS score (0-100):
    - Page Budget (Single Page): 20 pts
    - Contact Information: 20 pts (Email: 10 pts, Phone: 10 pts)
    - Core Sections: 60 pts (15 pts each for Education, Experience, Projects, Skills)
    """
    score = 0
    if is_single_page:
        score += 20

    if has_contact_info.get("email", False):
        score += 10
    if has_contact_info.get("phone", False):
        score += 10

    for sec in CORE_SECTIONS:
        if sec in sections_found:
            score += 15

    return min(100, max(0, score))


def strip_resume_markup(text: str) -> str:
    """
    Strips LaTeX commands, Markdown markers, and YAML frontmatter
    to extract plain selectable text for density analysis.
    """
    # Remove YAML frontmatter
    text = re.sub(r'^---\s*\n.*?\n---\s*\n', '', text, flags=re.DOTALL)
    # Remove LaTeX comments
    text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    # Remove LaTeX preamble and macros
    text = re.sub(r'\\(?:documentclass|usepackage|geometry|hypersetup|setlist|setlength|pagestyle|newcommand)\b.*?(\n|$)', '', text)
    # Remove LaTeX commands like \textbf{...}, \textit{...}, \cvsection{...}
    text = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?\{([^}]*)\}', r'\2', text)
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)
    # Remove Markdown headers and formatting
    text = re.sub(r'^[#]+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Normalize whitespace
    return re.sub(r'\s+', ' ', text).strip()


def scan_text_for_ats(text: str, file_path: str = "", vault_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Scans plain text, Markdown, or LaTeX resume source for ATS metrics,
    sections, contact info, and estimated single-page budget.
    """
    clean_text = strip_resume_markup(text)
    words = clean_text.split()
    word_count = len(words)
    char_count = len(clean_text)

    # In standard ATS formats, 1 page is approximately 250 to 750 words
    is_single_page = (word_count <= 800)
    page_count = 1 if is_single_page else max(2, int(round(word_count / 600.0 + 0.49)))

    sections_found = detect_sections(text)
    sections_missing = [sec for sec in CORE_SECTIONS if sec not in sections_found]
    has_contact_info = detect_contact_info(text)

    detected_placeholders = detect_placeholders(text)
    placeholders_detected = len(detected_placeholders) > 0
    background_status = check_vault_background(vault_root)

    warnings = []
    if placeholders_detected:
        ats_score = 0
        is_ready_for_application = False
        warnings.append(
            f"Abstract template placeholders detected ({', '.join(detected_placeholders[:4])}). "
            "Verified candidate background has not been ingested yet. "
            "Action required: Use 'add-experience-curriculum' or import past CV into 001-background/."
        )
    else:
        ats_score = calculate_ats_score(is_single_page, sections_found, has_contact_info)
        is_ready_for_application = (ats_score >= 70)

    if background_status.get("is_background_empty", False):
        warnings.append(
            "001-background/ has 0 verified experience or project notes. Candidate background is completely unpopulated."
        )

    if not is_single_page:
        warnings.append(
            f"Resume content word count ({word_count} words) likely exceeds 1 page. "
            "Early career resumes must be strictly 1 page (recommended: 350-700 words)."
        )

    for missing in sections_missing:
        warnings.append(f"Missing recommended core section: '{missing.capitalize()}'.")

    if not has_contact_info["email"]:
        warnings.append("Missing email contact information.")
    if not has_contact_info["phone"]:
        warnings.append("Missing phone number.")

    if word_count < 100:
        warnings.append(f"Low word count ({word_count} words). Resume may be sparse or empty.")
    elif is_single_page and word_count > 750:
        warnings.append(f"High word count ({word_count} words). Layout may be overly dense for 1 page.")

    density_metrics = {
        "word_count": word_count,
        "char_count": char_count,
        "words_per_page": round(word_count / max(1, page_count), 1),
        "density_status": "optimal" if (200 <= word_count <= 750 and is_single_page) else ("sparse" if word_count < 200 else "dense"),
    }

    return {
        "file_path": str(file_path),
        "is_single_page": is_single_page,
        "page_count": page_count,
        "word_count": word_count,
        "sections_found": sections_found,
        "sections_missing": sections_missing,
        "has_contact_info": has_contact_info,
        "placeholders_detected": placeholders_detected,
        "detected_placeholders": detected_placeholders,
        "background_status": background_status,
        "is_ready_for_application": is_ready_for_application,
        "density_metrics": density_metrics,
        "warnings": warnings,
        "ats_score": ats_score,
    }


def scan_pdf_for_ats(pdf_path: Union[str, Path], vault_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Scans a PDF resume using pdfplumber to evaluate ATS parseability,
    page count, section headers, contact information, and text density.
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber is required to scan PDF files. Install it via pip install pdfplumber.")

    pdf = pdfplumber.open(str(pdf_path))
    try:
        pages = pdf.pages if pdf and hasattr(pdf, "pages") else []
        page_count = len(pages)
        is_single_page = (page_count == 1)

        page_texts = []
        for page in pages:
            txt = page.extract_text() if hasattr(page, "extract_text") else ""
            page_texts.append(txt or "")

        full_text = "\n".join(page_texts)
        words = full_text.split()
        word_count = len(words)
        char_count = len(full_text)

        sections_found = detect_sections(full_text)
        sections_missing = [sec for sec in CORE_SECTIONS if sec not in sections_found]
        has_contact_info = detect_contact_info(full_text)

        detected_placeholders = detect_placeholders(full_text)
        placeholders_detected = len(detected_placeholders) > 0
        background_status = check_vault_background(vault_root)

        warnings = []
        if placeholders_detected:
            ats_score = 0
            is_ready_for_application = False
            warnings.append(
                f"Abstract template placeholders detected ({', '.join(detected_placeholders[:4])}). "
                "Verified candidate background has not been ingested yet. "
                "Action required: Use 'add-experience-curriculum' or import past CV into 001-background/."
            )
        else:
            ats_score = calculate_ats_score(is_single_page, sections_found, has_contact_info)
            is_ready_for_application = (ats_score >= 70)

        if background_status.get("is_background_empty", False):
            warnings.append(
                "001-background/ has 0 verified experience or project notes. Candidate background is completely unpopulated."
            )

        if not is_single_page:
            warnings.append(
                f"Resume exceeds 1 page (found {page_count} pages). "
                "Early career/student resumes must be strictly 1 page for ATS & recruiter review."
            )

        for missing in sections_missing:
            warnings.append(f"Missing recommended core section: '{missing.capitalize()}'.")

        if not has_contact_info["email"]:
            warnings.append("Missing email contact information.")
        if not has_contact_info["phone"]:
            warnings.append("Missing phone number.")

        if word_count < 100 and page_count > 0:
            warnings.append(f"Low word count ({word_count} words). Check if PDF text is selectable or rasterized.")
        elif is_single_page and word_count > 800:
            warnings.append(f"High word count ({word_count} words on 1 page). Layout may be overly dense.")

        density_metrics = {
            "word_count": word_count,
            "char_count": char_count,
            "words_per_page": round(word_count / max(1, page_count), 1),
            "density_status": "optimal" if (200 <= word_count <= 750 and is_single_page) else ("sparse" if word_count < 200 else "dense"),
        }

        return {
            "file_path": str(pdf_path),
            "is_single_page": is_single_page,
            "page_count": page_count,
            "word_count": word_count,
            "sections_found": sections_found,
            "sections_missing": sections_missing,
            "has_contact_info": has_contact_info,
            "placeholders_detected": placeholders_detected,
            "detected_placeholders": detected_placeholders,
            "background_status": background_status,
            "is_ready_for_application": is_ready_for_application,
            "density_metrics": density_metrics,
            "warnings": warnings,
            "ats_score": ats_score,
        }
    finally:
        if pdf and hasattr(pdf, "close"):
            try:
                pdf.close()
            except Exception:
                pass


def scan_resume(file_path: Union[str, Path], vault_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Universal scanner that dispatches to PDF scanner or text/markdown/tex scanner
    based on the file extension.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found at: {path}")

    ext = path.suffix.lower()
    if ext == ".pdf":
        return scan_pdf_for_ats(path, vault_root=vault_root)
    else:
        text_content = path.read_text(encoding="utf-8", errors="replace")
        return scan_text_for_ats(text_content, file_path=str(path), vault_root=vault_root)


def format_text_report(result: Dict[str, Any]) -> str:
    """Formats ATS scan result into a readable terminal report."""
    is_blocked = result.get("placeholders_detected", False)
    if is_blocked:
        score_display = "0/100 (BLOCKED - UNPOPULATED TEMPLATE)"
    else:
        score_display = f"{result['ats_score']}/100 ({'PASS' if result['ats_score'] >= 70 else 'FAIL'})"

    lines = [
        "=" * 60,
        f"ATS RESUME SCAN REPORT: {result['file_path']}",
        "=" * 60,
        f"ATS Score:        {score_display}",
    ]

    if is_blocked:
        bg = result.get("background_status", {})
        exp_count = bg.get("experiences_count", 0)
        proj_count = bg.get("projects_count", 0)
        lines.append("Template Status:  ABSTRACT PLACEHOLDERS DETECTED (Background Ingestion Required)")
        lines.append(f"Verified Records: {exp_count} experiences, {proj_count} projects in 001-background/")

    lines.extend([
        f"Page Count:       {result['page_count']} (Single Page: {'YES' if result['is_single_page'] else 'NO'})",
        f"Word Count:       {result['word_count']} words",
        f"Density Status:   {result['density_metrics']['density_status'].upper()}",
        f"Sections Found:   {', '.join(result['sections_found']) if result['sections_found'] else 'None'}",
        f"Sections Missing: {', '.join(result['sections_missing']) if result['sections_missing'] else 'None'}",
        "Contact Information:",
        f"  - Email:    {'[OK]' if result['has_contact_info']['email'] else '[MISSING]'}",
        f"  - Phone:    {'[OK]' if result['has_contact_info']['phone'] else '[MISSING]'}",
        f"  - GitHub:   {'[OK]' if result['has_contact_info']['github'] else '[NOT FOUND]'}",
        f"  - LinkedIn: {'[OK]' if result['has_contact_info']['linkedin'] else '[NOT FOUND]'}",
    ])

    if result.get("warnings") or is_blocked:
        lines.append("-" * 60)
        lines.append("Warnings & Action Items:")
        if is_blocked:
            lines.append("  • [MANDATORY NEXT STEP] Ingest your verified background into 001-background/ using the 'add-experience-curriculum' skill before tailoring CVs.")
        for w in result.get("warnings", []):
            lines.append(f"  • [!] {w}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    """Main CLI entry point for validate_ats."""
    parser = argparse.ArgumentParser(
        description="Validate PDF, LaTeX, or Markdown resume for ATS compliance and single-page budget."
    )
    parser.add_argument("file_positional", nargs="?", default=None, help="Path to resume file (PDF, TEX, MD, TXT)")
    parser.add_argument("--pdf", default=None, help="Path to PDF resume")
    parser.add_argument("--file", default=None, help="Path to resume file (PDF, TEX, MD, TXT)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--output", help="Write report to file")
    args = parser.parse_args()

    target = args.pdf or args.file or args.file_positional or "002-cv/resume.pdf"
    target_path = Path(target)

    if not target_path.exists():
        sys.stderr.write(f"Error: File not found: {target_path}\n")
        sys.exit(1)

    try:
        # If explicitly flagged as --pdf or file has .pdf suffix, use PDF scan
        if args.pdf or target_path.suffix.lower() == ".pdf":
            result = scan_pdf_for_ats(target_path)
        else:
            result = scan_resume(target_path)
    except ImportError as exc:
        if args.json:
            print(json.dumps({
                "success": False,
                "error": str(exc),
                "suggestion": "Run 'pip install pdfplumber' or scan Markdown (.md) or LaTeX (.tex) sources directly with zero dependencies."
            }))
        else:
            sys.stderr.write(f"\n[DEPENDENCY NOTE] {exc}\n")
            sys.stderr.write("Tip: You can scan Markdown (.md) or LaTeX (.tex) resume sources directly with zero dependencies:\n")
            sys.stderr.write("     python 002-cv/scripts/validate_ats.py 002-cv/template.tex\n\n")
        sys.exit(1)
    except Exception as exc:
        sys.stderr.write(f"Error scanning resume: {exc}\n")
        sys.exit(1)

    if args.json:
        output_content = json.dumps(result, indent=2)
    else:
        output_content = format_text_report(result)

    if args.output:
        out_file = Path(args.output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(output_content, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output_content)

    is_ready = result.get("is_ready_for_application", False)
    sys.exit(0 if (result["ats_score"] >= 70 and is_ready) else 1)


if __name__ == "__main__":
    main()

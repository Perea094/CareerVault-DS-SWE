#!/usr/bin/env python3
"""
validate_ats.py - ATS Resume Parseability Scanner

Validates compiled PDF resumes for ATS compliance, 1-page budget enforcement,
standard section headers, contact information parseability, and density metrics.
Uses pdfplumber to extract text and analyze layout structure.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Union

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


CORE_SECTIONS = ["education", "experience", "projects", "skills"]

SECTION_PATTERNS = {
    "education": re.compile(
        r"^\s*(?:[#•\-\d\.]+\s+)?(education|academic\s+background|education\s+&\s+honors|estudios|educaci[oó]n)\b",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^\s*(?:[#•\-\d\.]+\s+)?(experience|work\s+experience|professional\s+experience|employment\s+history|experiencia)\b",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^\s*(?:[#•\-\d\.]+\s+)?(projects|technical\s+projects|academic\s+projects|key\s+projects|proyectos)\b",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^\s*(?:[#•\-\d\.]+\s+)?(technical\s+skills|skills|skills\s+&\s+tools|technologies|tools\s+&\s+technologies|habilidades)\b",
        re.IGNORECASE,
    ),
}

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}")
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


def scan_pdf_for_ats(pdf_path: Union[str, Path]) -> Dict[str, Any]:
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

        warnings = []
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

        ats_score = calculate_ats_score(is_single_page, sections_found, has_contact_info)

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


def format_text_report(result: Dict[str, Any]) -> str:
    """Formats ATS scan result into a readable terminal report."""
    lines = [
        "=" * 60,
        f"ATS RESUME SCAN REPORT: {result['file_path']}",
        "=" * 60,
        f"ATS Score:        {result['ats_score']}/100 ({'PASS' if result['ats_score'] >= 70 else 'FAIL'})",
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
    ]
    if result["warnings"]:
        lines.append("-" * 60)
        lines.append("Warnings & Action Items:")
        for w in result["warnings"]:
            lines.append(f"  • [!] {w}")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    """Main CLI entry point for validate_ats."""
    parser = argparse.ArgumentParser(description="Validate PDF resume for ATS compliance and single-page budget.")
    parser.add_argument("pdf_positional", nargs="?", default=None, help="Path to PDF resume")
    parser.add_argument("--pdf", default=None, help="Path to PDF resume")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--output", help="Write report to file")
    args = parser.parse_args()

    pdf_target = args.pdf or args.pdf_positional or "002-cv/resume.pdf"
    target_path = Path(pdf_target)

    if not target_path.exists():
        sys.stderr.write(f"Error: PDF file not found: {target_path}\n")
        sys.exit(1)

    try:
        result = scan_pdf_for_ats(target_path)
    except Exception as exc:
        sys.stderr.write(f"Error scanning PDF: {exc}\n")
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

    sys.exit(0 if result["ats_score"] >= 70 else 1)


if __name__ == "__main__":
    main()

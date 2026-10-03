#!/usr/bin/env python3
"""
Dynamic LaTeX Resume Generator.
Renders ATS-compliant LaTeX resume files from templates, candidate profile dictionaries,
structured JSON resume data, or tailored Markdown CV drafts.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

# Attempt to import candidate_profile loader
try:
    from candidate_profile import load_profile  # type: ignore
except ImportError:
    background_dir = Path(__file__).resolve().parent.parent.parent / "001-background"
    if str(background_dir) not in sys.path:
        sys.path.insert(0, str(background_dir))
    try:
        from candidate_profile import load_profile  # type: ignore
    except ImportError:
        load_profile = None  # type: ignore

# Standard placeholder to profile field mapping
STANDARD_PLACEHOLDERS = {
    "NAME": "name",
    "LOCATION": "location",
    "EMAIL": "email",
    "PHONE": "phone",
    "LINKEDIN": "linkedin",
    "GITHUB": "github",
    "SCHOOL": "school",
    "SCHOOL_LOCATION": "school_location",
    "DEGREE": "degree",
    "GRADUATION": "graduation",
    "GPA": "gpa",
    "DISTINCTIONS": "distinctions",
    "COURSEWORK": "coursework",
}

DEFAULT_PLACEHOLDER_VALUES = {
    "NAME": "Candidate Name",
    "LOCATION": "City, Country",
    "EMAIL": "candidate@example.com",
    "PHONE": "+1 555 0100",
    "LINKEDIN": "https://linkedin.com/in/username",
    "GITHUB": "https://github.com/username",
    "SCHOOL": "University",
    "SCHOOL_LOCATION": "City, Country",
    "DEGREE": "B.S. in Computer Science / Data Science",
    "GRADUATION": "May 2027",
    "GPA": "3.9/4.0",
    "DISTINCTIONS": "Dean's Honors List, Academic Excellence Scholarship",
    "COURSEWORK": "Distributed Systems, Machine Learning, Deep Learning, Algorithms \\& Data Structures, Database Systems, Computer Systems, Linear Algebra, Probability \\& Statistics",
}

# LaTeX characters that must be escaped
LATEX_ESCAPE_REGEX = re.compile(r'(?<!\\)([&%$#_])')

DEFAULT_DOCUMENT_PREAMBLE = r"""\documentclass[10pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage{mathptmx} % Standard Times New Roman font for ATS compliance & compact density
\usepackage{geometry}
\geometry{letterpaper, left=0.4in, right=0.4in, top=0.35in, bottom=0.35in, nohead, nofoot}
\usepackage{hyperref}
\hypersetup{
    colorlinks=true,
    linkcolor=black,
    urlcolor=blue,
}
\usepackage{enumitem}
\setlist[itemize]{leftmargin=11pt, label={\small$\bullet$}, itemsep=0.5pt, topsep=1pt, parsep=0pt, partopsep=0pt}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\pagestyle{empty} % Strictly no headers or footers / no page numbers

% Clean, compact section macro with thin divider
\newcommand{\cvsection}[1]{%
  \vspace{3.5pt}%
  {\small\textbf{\MakeUppercase{#1}}}\\[-3.5pt]%
  \rule{\textwidth}{0.4pt}\par\vspace{2pt}%
}

\begin{document}
"""

DEFAULT_DOCUMENT_POSTAMBLE = r"""
\end{document}
"""


def escape_latex(text: Any) -> str:
    """
    Escapes LaTeX special characters: &, %, $, #, _.
    Preserves already-escaped sequences.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return LATEX_ESCAPE_REGEX.sub(r'\\\1', text)


def markdown_inline_to_latex(text: str) -> str:
    """
    Converts inline markdown formatting (**bold**, *italic*, [link](url), `code`) to LaTeX.
    Preserves math blocks and special symbols.
    """
    if not text:
        return ""

    # Preserve explicit math blocks like $...$
    math_segments: List[str] = []

    def save_math(match: re.Match) -> str:
        math_segments.append(match.group(0))
        return f"XYZMATHSEGMENTXYZ{len(math_segments) - 1}XYZ"

    text = re.sub(r'\$[^\$]+\$', save_math, text)

    # Preserve links [label](url)
    link_segments: List[str] = []

    def save_link(match: re.Match) -> str:
        label = escape_latex(match.group(1))
        url = match.group(2)
        link_segments.append(f"\\href{{{url}}}{{{label}}}")
        return f"XYZLINKSEGMENTXYZ{len(link_segments) - 1}XYZ"

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', save_link, text)

    # Convert approx numbers (~3,500 -> $\sim$3,500)
    text = re.sub(r'(?<=\s)~(\d)', r'$\\sim$\1', text)
    text = re.sub(r'^~(\d)', r'$\\sim$\1', text)

    # Escape general text characters
    text = escape_latex(text)

    # Convert bold: **text** -> \textbf{text}
    text = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)

    # Convert italic: *text* -> \textit{text} or _text_ -> \textit{text}
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\\textit{\1}', text)
    text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'\\textit{\1}', text)

    # Convert code: `code` -> \texttt{code}
    text = re.sub(r'`([^`]+)`', r'\\texttt{\1}', text)

    # Restore links
    for idx, seg in enumerate(link_segments):
        text = text.replace(f"XYZLINKSEGMENTXYZ{idx}XYZ", seg)

    # Restore math
    for idx, seg in enumerate(math_segments):
        text = text.replace(f"XYZMATHSEGMENTXYZ{idx}XYZ", seg)

    return text


def render_template_string(template_content: str, profile: Dict[str, Any], auto_escape: bool = True) -> str:
    """
    Renders a LaTeX template string by replacing <<PLACEHOLDER>> markers
    with corresponding candidate profile fields.
    Falls back to sensible defaults when optional fields are omitted.
    """
    if not template_content:
        return ""
    if not profile:
        profile = {}

    rendered = template_content

    # Build case-insensitive lookup
    profile_lookup = {k.lower().strip(): v for k, v in profile.items()}

    # Process standard placeholders first
    for placeholder_name, key in STANDARD_PLACEHOLDERS.items():
        tag = f"<<{placeholder_name}>>"
        if tag in rendered:
            val = profile.get(key)
            if val is None:
                val = profile_lookup.get(key.lower())
            if val is None:
                val = profile_lookup.get(placeholder_name.lower())

            # Elastic fallbacks
            if val is None and placeholder_name == "SCHOOL_LOCATION":
                val = profile.get("location") or profile_lookup.get("location")
            if val is None:
                val = DEFAULT_PLACEHOLDER_VALUES.get(placeholder_name)

            if val is not None:
                val_str = str(val)
                # Avoid escaping full URLs
                is_url = placeholder_name in ("LINKEDIN", "GITHUB") or val_str.startswith("http://") or val_str.startswith("https://")
                if auto_escape and not is_url:
                    val_str = escape_latex(val_str)
                rendered = rendered.replace(tag, val_str)

    # Process any additional <<KEY>> placeholders present in profile
    for k, v in profile.items():
        tag = f"<<{k.upper()}>>"
        if tag in rendered:
            val_str = str(v)
            is_url = val_str.startswith("http://") or val_str.startswith("https://")
            if auto_escape and not is_url:
                val_str = escape_latex(val_str)
            rendered = rendered.replace(tag, val_str)

    # Clean up empty optional markers if needed
    if profile.get("gpa") == "":
        rendered = rendered.replace(r"\textbullet\ \textbf{GPA: }", "")
    if profile.get("distinctions") == "":
        rendered = re.sub(r'\\textbf\{Distinctions:\}\s*\\\\\n?', '', rendered)

    return rendered


def parse_markdown_resume(markdown_content: str) -> Dict[str, Any]:
    """
    Parses a tailored Markdown resume into structured components:
    frontmatter metadata, candidate name, contact line, and section chunks.
    """
    lines = markdown_content.strip().splitlines()
    data: Dict[str, Any] = {
        "metadata": {},
        "name": "",
        "contact_line": "",
        "sections": []
    }

    # Extract YAML frontmatter
    idx = 0
    if lines and lines[0].strip() == "---":
        idx = 1
        frontmatter_lines = []
        while idx < len(lines) and lines[idx].strip() != "---":
            frontmatter_lines.append(lines[idx])
            idx += 1
        idx += 1  # Skip closing ---
        
        # Simple key-value parser for flat YAML frontmatter
        for fline in frontmatter_lines:
            fline = fline.strip()
            if ":" in fline:
                k, v = fline.split(":", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                data["metadata"][k] = v

    if data["metadata"].get("candidate"):
        data["name"] = data["metadata"]["candidate"]

    # Iterate remaining lines
    current_section: Optional[Dict[str, Any]] = None
    first_non_empty = True

    while idx < len(lines):
        line = lines[idx].strip()
        idx += 1

        if not line or line == "---":
            continue

        # Candidate name heading
        if line.startswith("# ") and not data["name"]:
            data["name"] = line[2:].strip()
            continue

        # Contact line right below name
        if not data["contact_line"] and (data["name"] or first_non_empty) and not line.startswith("#"):
            if "@" in line or "•" in line or "|" in line or "http" in line:
                data["contact_line"] = line
                first_non_empty = False
                continue

        first_non_empty = False

        # Section headings (## Section Title)
        if line.startswith("## "):
            section_title = line[3:].strip()
            current_section = {
                "title": section_title,
                "content_lines": []
            }
            data["sections"].append(current_section)
            continue

        if current_section is not None:
            current_section["content_lines"].append(line)

    return data


def render_markdown_to_tex(markdown_content: str, template_path: Optional[Union[str, Path]] = None) -> str:
    """
    Converts a Markdown CV draft into an ATS-compliant LaTeX resume string.
    """
    parsed = parse_markdown_resume(markdown_content)
    name = parsed["name"] or "Candidate Name"
    contact_line = parsed["contact_line"]

    out_lines = [DEFAULT_DOCUMENT_PREAMBLE]

    # --- HEADER ---
    out_lines.append("% --- HEADER ---")
    out_lines.append(r"\begin{center}")
    out_lines.append(f"    {{\\LARGE \\textbf{{{escape_latex(name)}}}}}\\\\[2pt]")

    # Contact line formatting
    if contact_line:
        # Split tokens by • or | or \textbullet
        tokens = [t.strip() for t in re.split(r'[•|]', contact_line) if t.strip()]
        formatted_tokens = []
        for token in tokens:
            # Check for markdown link [Label](url)
            link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', token)
            if link_match:
                lbl = escape_latex(link_match.group(1))
                url = link_match.group(2)
                formatted_tokens.append(f"\\href{{{url}}}{{{lbl}}}")
            elif "@" in token:
                clean_email = token.strip()
                formatted_tokens.append(f"\\href{{mailto:{clean_email}}}{{{clean_email}}}")
            else:
                formatted_tokens.append(escape_latex(token))

        joined_contact = r" \textbullet\ ".join(formatted_tokens)
        out_lines.append(f"    \\small {joined_contact}")
    out_lines.append(r"\end{center}")
    out_lines.append(r"\vspace{-6pt}")

    # Process Sections
    for section in parsed["sections"]:
        title = section["title"]
        lines = section["content_lines"]

        out_lines.append(f"\n% --- {title.upper()} ---")
        out_lines.append(f"\\cvsection{{{escape_latex(title)}}}")

        in_itemize = False

        for line in lines:
            # Bullet point
            if line.startswith("- ") or line.startswith("* "):
                if not in_itemize:
                    out_lines.append(r"\begin{itemize}")
                    in_itemize = True
                bullet_text = line[2:].strip()
                formatted_bullet = markdown_inline_to_latex(bullet_text)
                out_lines.append(f"    \\item {formatted_bullet}")
            else:
                if in_itemize:
                    out_lines.append(r"\end{itemize}")
                    in_itemize = False

                # Handle header/institution lines
                if "—" in line or "--" in line:
                    parts = re.split(r'—|--', line, maxsplit=1)
                    left = markdown_inline_to_latex(parts[0].strip())
                    right = markdown_inline_to_latex(parts[1].strip())
                    out_lines.append(f"{left} \\hfill {right}\\\\")
                else:
                    formatted_line = markdown_inline_to_latex(line)
                    out_lines.append(f"{formatted_line}\\\\")

        if in_itemize:
            out_lines.append(r"\end{itemize}")

    out_lines.append(DEFAULT_DOCUMENT_POSTAMBLE)
    return "\n".join(out_lines)


def render_json_resume_to_tex(resume_data: Dict[str, Any]) -> str:
    """
    Renders structured resume JSON into ATS-compliant LaTeX.
    Supports standard JSON resume schema (basics, education, work, projects, skills).
    """
    basics = resume_data.get("basics") or resume_data.get("candidate") or {}
    name = basics.get("name", "Candidate Name")
    location = basics.get("location", "City, Country")
    email = basics.get("email", basics.get("email_contact", "candidate@example.com"))
    phone = basics.get("phone", "+1 555 0100")
    linkedin = basics.get("linkedin", "https://linkedin.com")
    github = basics.get("github", "https://github.com")

    out_lines = [DEFAULT_DOCUMENT_PREAMBLE]

    # Header
    out_lines.append("% --- HEADER ---")
    out_lines.append(r"\begin{center}")
    out_lines.append(f"    {{\\LARGE \\textbf{{{escape_latex(name)}}}}}\\\\[2pt]")
    out_lines.append(
        f"    \\small {escape_latex(location)} \\textbullet\\ "
        f"\\href{{mailto:{email}}}{{{email}}} \\textbullet\\ "
        f"{escape_latex(phone)} \\textbullet\\ "
        f"\\href{{{linkedin}}}{{LinkedIn}} \\textbullet\\ "
        f"\\href{{{github}}}{{GitHub}}"
    )
    out_lines.append(r"\end{center}")
    out_lines.append(r"\vspace{-6pt}")

    # Education
    education_entries = resume_data.get("education") or []
    if education_entries:
        out_lines.append("\n% --- EDUCATION ---")
        out_lines.append(r"\cvsection{Education}")
        for edu in education_entries:
            school = escape_latex(edu.get("institution") or edu.get("school") or "University")
            school_loc = escape_latex(edu.get("location") or location)
            degree = escape_latex(edu.get("degree") or edu.get("studyType") or "B.S. in Computer Science")
            grad = escape_latex(edu.get("graduation") or edu.get("endDate") or "May 2027")
            gpa = edu.get("gpa") or edu.get("score")
            gpa_str = f" \\textbullet\\ \\textbf{{GPA: {escape_latex(gpa)}}}" if gpa else ""

            out_lines.append(f"\\textbf{{{school}}} \\hfill {school_loc}\\\\")
            out_lines.append(f"\\textit{{{degree}}}{gpa_str} \\hfill {grad}\\\\")
            if edu.get("distinctions") or edu.get("honors"):
                honors = ", ".join(edu.get("distinctions") or edu.get("honors"))
                out_lines.append(f"\\textbf{{Distinctions:}} {escape_latex(honors)}\\\\")
            if edu.get("coursework"):
                cw = ", ".join(edu["coursework"]) if isinstance(edu["coursework"], list) else str(edu["coursework"])
                out_lines.append(f"\\textbf{{Selected Coursework:}} {escape_latex(cw)}")

    # Experience / Work
    work_entries = resume_data.get("work") or resume_data.get("experience") or []
    if work_entries:
        out_lines.append("\n% --- EXPERIENCE ---")
        out_lines.append(r"\cvsection{Experience}")
        for idx, work in enumerate(work_entries):
            if idx > 0:
                out_lines.append(r"\vspace{2pt}")
            company = escape_latex(work.get("company") or work.get("name") or "Company")
            work_loc = escape_latex(work.get("location") or location)
            role = escape_latex(work.get("role") or work.get("position") or "Software Engineer")
            dates = escape_latex(work.get("dates") or f"{work.get('startDate', '')} – {work.get('endDate', '')}".strip(" –"))

            out_lines.append(f"\\textbf{{{company}}} \\hfill {work_loc}\\\\")
            out_lines.append(f"\\textit{{{role}}} \\hfill {dates}")

            bullets = work.get("bullets") or work.get("highlights") or []
            if bullets:
                out_lines.append(r"\begin{itemize}")
                for b in bullets:
                    out_lines.append(f"    \\item {markdown_inline_to_latex(b)}")
                out_lines.append(r"\end{itemize}")

    # Projects
    projects = resume_data.get("projects") or []
    if projects:
        out_lines.append("\n% --- PROJECTS ---")
        out_lines.append(r"\cvsection{Projects}")
        for idx, proj in enumerate(projects):
            if idx > 0:
                out_lines.append(r"\vspace{2pt}")
            proj_name = escape_latex(proj.get("name") or "Project Name")
            tech = escape_latex(proj.get("technologies") or proj.get("stack") or "")
            tech_str = f" \\textbar\\ \\textit{{{tech}}}" if tech else ""
            link = proj.get("link") or proj.get("url") or ""
            link_str = f" \\hfill \\href{{{link}}}{{\\small GitHub}}" if link else ""
            dates = proj.get("dates") or proj.get("date") or ""
            date_str = f" \\textbullet\\ {escape_latex(dates)}" if (link_str and dates) else (f" \\hfill {escape_latex(dates)}" if dates else "")

            out_lines.append(f"\\textbf{{{proj_name}}}{tech_str}{link_str}{date_str}")
            bullets = proj.get("bullets") or proj.get("highlights") or []
            if bullets:
                out_lines.append(r"\begin{itemize}")
                for b in bullets:
                    out_lines.append(f"    \\item {markdown_inline_to_latex(b)}")
                out_lines.append(r"\end{itemize}")

    # Skills
    skills = resume_data.get("skills") or {}
    if skills:
        out_lines.append("\n% --- TECHNICAL SKILLS ---")
        out_lines.append(r"\cvsection{Technical Skills}")
        if isinstance(skills, dict):
            for cat, items in skills.items():
                items_str = ", ".join(items) if isinstance(items, list) else str(items)
                out_lines.append(f"\\textbf{{{escape_latex(cat)}:}} {escape_latex(items_str)}\\\\")
        elif isinstance(skills, list):
            for skill_obj in skills:
                cat = skill_obj.get("name", "Skills")
                keywords = ", ".join(skill_obj.get("keywords", []))
                out_lines.append(f"\\textbf{{{escape_latex(cat)}:}} {escape_latex(keywords)}\\\\")

    out_lines.append(DEFAULT_DOCUMENT_POSTAMBLE)
    return "\n".join(out_lines)


def generate_resume(
    template_path: Union[str, Path],
    output_path: Union[str, Path],
    profile: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Loads LaTeX template, replaces placeholders with candidate profile data,
    and writes out the compiled .tex file.
    """
    template_file = Path(template_path)
    output_file = Path(output_path)

    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found at: {template_file}")

    if profile is None:
        if load_profile is not None:
            profile = load_profile()
        else:
            profile = {}

    template_content = template_file.read_text(encoding="utf-8")
    rendered_tex = render_template_string(template_content, profile)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(rendered_tex, encoding="utf-8")

    return output_file


def generate_from_markdown(
    markdown_path: Union[str, Path],
    output_path: Union[str, Path],
    template_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Parses a Markdown CV draft and compiles an ATS-compliant LaTeX resume file.
    """
    md_file = Path(markdown_path)
    output_file = Path(output_path)

    if not md_file.exists():
        raise FileNotFoundError(f"Markdown CV draft not found at: {md_file}")

    md_content = md_file.read_text(encoding="utf-8")
    rendered_tex = render_markdown_to_tex(md_content, template_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(rendered_tex, encoding="utf-8")

    return output_file


def generate_from_json(
    json_path: Union[str, Path],
    output_path: Union[str, Path],
    template_path: Optional[Union[str, Path]] = None
) -> Path:
    """
    Generates ATS-compliant LaTeX resume from structured resume JSON or profile JSON.
    """
    j_file = Path(json_path)
    output_file = Path(output_path)

    if not j_file.exists():
        raise FileNotFoundError(f"JSON resume file not found at: {j_file}")

    with open(j_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check if structured resume
    if any(k in data for k in ("work", "experience", "projects", "education")):
        rendered_tex = render_json_resume_to_tex(data)
    else:
        # Candidate profile dictionary
        template = Path(template_path) if template_path else Path(__file__).resolve().parent.parent / "template.tex"
        return generate_resume(template, output_path, data)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(rendered_tex, encoding="utf-8")

    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate ATS-compliant LaTeX resume from template, candidate profile, Markdown CV, or JSON."
    )
    parser.add_argument(
        "--template",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "template.tex"),
        help="Path to template.tex file (default: 002-cv/template.tex)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "Candidate_Resume.tex"),
        help="Path to target .tex file (default: 002-cv/Candidate_Resume.tex)"
    )
    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Path to preferences.json or profile JSON"
    )
    parser.add_argument(
        "--markdown", "-m",
        type=str,
        default=None,
        help="Path to tailored markdown resume draft (.md)"
    )
    parser.add_argument(
        "--json", "-j",
        type=str,
        default=None,
        help="Path to structured resume JSON file"
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output machine-readable JSON status for AI agents"
    )

    args = parser.parse_args()

    try:
        if args.markdown:
            out = generate_from_markdown(args.markdown, args.output, args.template)
            source_type = "markdown"
        elif args.json:
            out = generate_from_json(args.json, args.output, args.template)
            source_type = "json"
        else:
            prof = None
            if args.profile:
                if load_profile is not None:
                    prof = load_profile(args.profile)
                else:
                    with open(args.profile, "r", encoding="utf-8") as f:
                        prof = json.load(f)
            out = generate_resume(args.template, args.output, prof)
            source_type = "template_profile"

        if args.json_output:
            print(json.dumps({
                "success": True,
                "output_path": str(out.resolve()),
                "source_type": source_type
            }))
        else:
            print(f"Successfully generated LaTeX resume at: {out}")
    except Exception as exc:
        if args.json_output:
            print(json.dumps({"success": False, "error": str(exc)}))
        else:
            print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

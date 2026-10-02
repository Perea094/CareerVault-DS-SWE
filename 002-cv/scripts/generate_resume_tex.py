#!/usr/bin/env python3
"""
Dynamic LaTeX Resume Generator.
Renders ATS-compliant LaTeX resume files from templates by dynamically injecting
candidate profile information (name, contact links, university, graduation date, etc.).
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Union

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
    "DEGREE": "degree",
    "GRADUATION": "graduation",
}

# LaTeX characters that must be escaped
LATEX_ESCAPE_REGEX = re.compile(r'(?<!\\)([&%$#_])')


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


def render_template_string(template_content: str, profile: Dict[str, Any], auto_escape: bool = True) -> str:
    """
    Renders a LaTeX template string by replacing <<PLACEHOLDER>> markers
    with corresponding candidate profile fields.
    
    Standard markers supported:
    <<NAME>>, <<LOCATION>>, <<EMAIL>>, <<PHONE>>, <<LINKEDIN>>, <<GITHUB>>,
    <<SCHOOL>>, <<DEGREE>>, <<GRADUATION>>
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

    return rendered


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


def main():
    parser = argparse.ArgumentParser(description="Generate ATS-compliant LaTeX resume from template and profile.")
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
        help="Optional path to custom preferences.json profile"
    )

    args = parser.parse_args()

    prof = None
    if args.profile:
        if load_profile is not None:
            prof = load_profile(args.profile)

    out = generate_resume(args.template, args.output, prof)
    print(f"Successfully generated LaTeX resume at: {out}")


if __name__ == "__main__":
    main()

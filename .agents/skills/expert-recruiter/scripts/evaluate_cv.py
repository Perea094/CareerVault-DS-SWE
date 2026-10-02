#!/usr/bin/env python3
"""
evaluate_cv.py - Automated CV & Job Opportunity Analyzer

Analyzes Markdown CVs for ATS compliance, metric-driven impact (XYZ formula),
action verb strength, and keyword overlap against target job descriptions.
Zero external dependencies (pure Python standard library).
"""

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# Action Verb Taxonomies
WEAK_ACTION_VERBS = {
    "helped", "assisted", "worked on", "responsible for", "participated in",
    "collaborated on", "handled", "involved in", "supported", "attempted",
    "contributed to", "aided", "served as"
}

STRONG_ACTION_VERBS = {
    "architected", "engineered", "spearheaded", "orchestrated", "developed",
    "designed", "optimized", "implemented", "deployed", "scaled", "automated",
    "trained", "fine-tuned", "accelerated", "reduced", "increased", "maximized",
    "minimized", "streamlined", "built", "founded", "co-founded", "authored",
    "formulated", "benchmarked", "refactored", "integrated", "eliminated"
}

# Regex for Quantifiable Metrics (XYZ formula detection)
METRIC_PATTERNS = [
    r"\b\d+%",                                    # Percentages: 94%, 25%
    r"\$\d+(?:[.,]\d+)?\b",                       # Currency: $20, $100k
    r"\b\d+\s*(?:ms|seconds|minutes|hours|days|weeks|months|years)\b",  # Latency / Time
    r"\b\d+(?:\.\d+)?(?:k|K|M|B|x|X)\b",         # Scale / Multipliers: 10k, 2x, 5M
    r"\b\d+\s*(?:users|clients|students|requests|fps|parameters|tokens|nodes|samples|models)\b",
    r"\b(?:first|1st|2nd|3rd)\s+place\b",         # Rankings / Awards
    r"\b\d+/\d+\b",                               # Scores / GPAs: 94/100, 4.0/4.0
    r"\b~?\d{2,}\b"                               # Arbitrary count: ~30, 150
]

COMMON_TECH_PATTERNS = [
    r"\bpython\b", r"\bc\+\+\b", r"\bc#\b", r"\brust\b", r"\bgo\b", r"\bjava\b",
    r"\bpytorch\b", r"\btensorflow\b", r"\bkeras\b", r"\bscikit-learn\b", r"\bopencv\b",
    r"\bgymnasium\b", r"\bgym-retro\b", r"\bhugging\s*face\b", r"\btransformers\b",
    r"\bllm\b", r"\bgenai\b", r"\brl\b", r"\breinforcement\s*learning\b", r"\bnlp\b",
    r"\bcomputer\s*vision\b", r"\bmlops\b", r"\bdocker\b", r"\bkubernetes\b",
    r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bsql\b", r"\bpostgres\b", r"\bmongodb\b",
    r"\braylib\b", r"\bgodot\b", r"\bhailo-8\b", r"\braspberry\s*pi\b", r"\blinux\b",
    r"\bgit\b", r"\bci/cd\b", r"\boptuna\b", r"\bprompt\s*engineering\b", r"\brag\b",
    r"\bvector\s*database\b", r"\blatex\b", r"\br\b", r"\bmatlab\b"
]


def parse_cv_sections(cv_text: str):
    """Parses markdown CV into sections, bullet points, and plain text."""
    lines = cv_text.splitlines()
    sections = {}
    current_section = "Header"
    sections[current_section] = []

    for line in lines:
        stripped = line.strip()
        header_match = re.match(r"^#{1,3}\s+(.+)$", stripped)
        if header_match:
            current_section = header_match.group(1).strip()
            sections[current_section] = []
        else:
            sections[current_section].append(line)

    bullet_points = []
    bullet_regex = re.compile(r"^[-*•]\s+(.+)$")
    for section_name, sec_lines in sections.items():
        for line in sec_lines:
            m = bullet_regex.match(line.strip())
            if m:
                bullet_points.append({
                    "section": section_name,
                    "text": m.group(1).strip()
                })

    return sections, bullet_points


def analyze_bullets(bullet_points):
    """Analyzes bullet points for metric usage and action verbs."""
    metric_regex = re.compile("|".join(METRIC_PATTERNS), re.IGNORECASE)
    analyzed = []
    metric_count = 0
    weak_verbs_found = []
    strong_verbs_found = []

    for b in bullet_points:
        text = b["text"]
        has_metric = bool(metric_regex.search(text))
        if has_metric:
            metric_count += 1

        first_words = " ".join(re.findall(r"\b[A-Za-z\-]+\b", text.lower())[:3])
        first_word = first_words.split()[0] if first_words else ""

        verb_status = "neutral"
        for weak in WEAK_ACTION_VERBS:
            if first_words.startswith(weak):
                verb_status = "weak"
                weak_verbs_found.append((b, weak))
                break

        if verb_status != "weak":
            for strong in STRONG_ACTION_VERBS:
                if first_words.startswith(strong):
                    verb_status = "strong"
                    strong_verbs_found.append((b, strong))
                    break

        analyzed.append({
            "section": b["section"],
            "text": text,
            "has_metric": has_metric,
            "verb_status": verb_status,
            "first_word": first_word
        })

    total_bullets = len(bullet_points)
    metric_ratio = (metric_count / total_bullets * 100) if total_bullets > 0 else 0.0

    return {
        "total_bullets": total_bullets,
        "quantified_bullets": metric_count,
        "quantified_percentage": round(metric_ratio, 1),
        "weak_starters_count": len(weak_verbs_found),
        "strong_starters_count": len(strong_verbs_found),
        "bullets_analysis": analyzed
    }


STOP_ACRONYMS = {
    "and", "the", "for", "with", "from", "both", "well", "gpa", "para",
    "note", "id", "us", "usa", "cfr", "eeo", "all", "not", "any", "are",
    "our", "you", "who", "how", "what", "when", "why", "per", "via"
}


def extract_keywords(text: str):
    """Extracts domain and technology keywords from text."""
    found = set()
    for pat in COMMON_TECH_PATTERNS:
        matches = re.findall(pat, text, re.IGNORECASE)
        for m in matches:
            found.add(m.lower().strip())
    
    # Also capture capitalized acronyms / technical terms
    acronyms = set(re.findall(r"\b[A-Z]{2,6}\b", text))
    for ac in acronyms:
        lower_ac = ac.lower()
        if lower_ac not in STOP_ACRONYMS and len(lower_ac) >= 2:
            found.add(lower_ac)

    return found


def compare_with_jd(cv_text: str, jd_text: str):
    """Compares CV keywords against a target job description."""
    cv_keywords = extract_keywords(cv_text)
    jd_keywords = extract_keywords(jd_text)

    matched = sorted(list(jd_keywords.intersection(cv_keywords)))
    missing = sorted(list(jd_keywords.difference(cv_keywords)))

    coverage = (len(matched) / len(jd_keywords) * 100) if jd_keywords else 100.0

    visa_flag = False
    remote_flag = False
    for line in jd_text.lower().splitlines():
        if any(w in line for w in ["visa", "sponsorship", "citizen", "authorized to work", "work authorization"]):
            visa_flag = True
        if any(w in line for w in ["remote", "hybrid", "on-site", "relocation"]):
            remote_flag = True

    return {
        "jd_keywords_total": len(jd_keywords),
        "matched_keywords_count": len(matched),
        "missing_keywords_count": len(missing),
        "keyword_coverage_pct": round(coverage, 1),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "flags": {
            "contains_visa_or_auth_clauses": visa_flag,
            "contains_location_or_remote_clauses": remote_flag
        }
    }


def compute_health_score(bullet_stats, jd_comparison=None):
    """Computes a baseline algorithmic score (0-100) prior to recruiter qualitative audit."""
    score = 0.0

    # 1. Metric / Quantifiability (Max 35 pts)
    metric_pct = bullet_stats["quantified_percentage"]
    score += min(35.0, (metric_pct / 60.0) * 35.0)

    # 2. Action Verb Rigor (Max 25 pts)
    total = max(1, bullet_stats["total_bullets"])
    strong_ratio = bullet_stats["strong_starters_count"] / total
    weak_ratio = bullet_stats["weak_starters_count"] / total
    verb_score = (strong_ratio * 25.0) - (weak_ratio * 15.0)
    score += max(5.0, min(25.0, 15.0 + verb_score))

    # 3. Content Volume & Structure (Max 20 pts)
    if 10 <= total <= 25:
        score += 20.0
    elif total < 10:
        score += (total / 10.0) * 20.0
    else:
        score += max(10.0, 20.0 - (total - 25) * 1.0)

    # 4. Keyword / Job-Fit Alignment (Max 20 pts)
    if jd_comparison:
        cov = jd_comparison["keyword_coverage_pct"]
        score += (cov / 100.0) * 20.0
    else:
        score += 15.0

    return round(score, 1)


def format_markdown_report(cv_path, jd_path, bullet_stats, jd_comp, score):
    """Generates a clean terminal / markdown summary string."""
    verdict = "PASS" if score >= 80 else ("BORDERLINE" if score >= 65 else "NEEDS REVISION")
    
    out = []
    out.append("=" * 60)
    out.append(f"EXPERT RECRUITER AUDIT: {os.path.basename(cv_path)}")
    out.append("=" * 60)
    out.append(f"- Baseline Metric Score: {score}/100")
    out.append(f"- Automated Verdict:     {verdict}")
    out.append(f"- Total Bullet Points:   {bullet_stats['total_bullets']}")
    out.append(f"- Quantified Bullets:    {bullet_stats['quantified_bullets']} ({bullet_stats['quantified_percentage']}%)")
    out.append(f"- Strong Action Verbs:   {bullet_stats['strong_starters_count']}")
    out.append(f"- Weak Action Starters:  {bullet_stats['weak_starters_count']}")

    if jd_comp:
        out.append("-" * 60)
        out.append(f"TARGET JOB MATCH: {os.path.basename(jd_path)}")
        out.append(f"- Keyword Coverage:      {jd_comp['keyword_coverage_pct']}% ({jd_comp['matched_keywords_count']}/{jd_comp['jd_keywords_total']})")
        if jd_comp['missing_keywords']:
            out.append(f"- Missing Keywords:      {', '.join(jd_comp['missing_keywords'][:12])}" + ("..." if len(jd_comp['missing_keywords']) > 12 else ""))
        if jd_comp['flags']['contains_visa_or_auth_clauses']:
            out.append("- [!] Attention: Job posting mentions work authorization/visa criteria.")
        if jd_comp['flags']['contains_location_or_remote_clauses']:
            out.append("- [!] Attention: Job posting specifies remote/location/relocation criteria.")

    out.append("=" * 60)
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Evaluate CV impact metrics, structure, and JD match.")
    parser.add_argument("--cv", required=True, help="Path to markdown CV file")
    parser.add_argument("--jd", required=False, help="Path to markdown Job Description file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")
    parser.add_argument("--output", help="Write report to specified output path")

    args = parser.parse_args()

    cv_path = Path(args.cv)
    if not cv_path.exists():
        sys.stderr.write(f"Error: CV file not found: {cv_path}\n")
        sys.exit(1)

    cv_text = cv_path.read_text(encoding="utf-8")
    sections, bullet_points = parse_cv_sections(cv_text)
    bullet_stats = analyze_bullets(bullet_points)

    jd_comp = None
    if args.jd:
        jd_path = Path(args.jd)
        if not jd_path.exists():
            sys.stderr.write(f"Error: Job description file not found: {jd_path}\n")
            sys.exit(1)
        jd_text = jd_path.read_text(encoding="utf-8")
        jd_comp = compare_with_jd(cv_text, jd_text)

    score = compute_health_score(bullet_stats, jd_comp)

    result_data = {
        "cv_path": str(cv_path),
        "jd_path": str(args.jd) if args.jd else None,
        "score": score,
        "verdict": "PASS" if score >= 80 else ("BORDERLINE" if score >= 65 else "NEEDS REVISION"),
        "bullet_stats": bullet_stats,
        "jd_comparison": jd_comp
    }

    if args.json:
        out_str = json.dumps(result_data, indent=2)
    else:
        out_str = format_markdown_report(cv_path, args.jd, bullet_stats, jd_comp, score)

    if args.output:
        out_file = Path(args.output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(out_str, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(out_str)


if __name__ == "__main__":
    main()

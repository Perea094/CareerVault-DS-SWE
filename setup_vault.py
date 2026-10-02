#!/usr/bin/env python3
"""
Career Vault Onboarding & Setup Wizard.
Initializes and personalizes the Career Vault for Data Science and Software Engineering candidates.
Configures 001-background/preferences.json, syncs preferences.md, and generates a personalized LaTeX CV.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any

# Ensure 002-cv/scripts is in path for dynamic resume templating
CV_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "002-cv", "scripts"))
if CV_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, CV_SCRIPTS_DIR)

try:
    import generate_resume_tex
except ImportError:
    generate_resume_tex = None

DEFAULT_AVAILABILITY_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DEFAULT_SLOTS = [
    "06_00", "06_30", "07_00", "07_30", "08_00", "08_30", "09_00", "09_30",
    "10_00", "10_30", "11_00", "11_30", "12_00", "12_30", "13_00", "13_30",
    "14_00", "14_30", "15_00", "15_30", "16_00", "16_30", "17_00", "17_30",
    "18_00", "18_30", "19_00", "19_30", "20_00", "20_30", "21_00", "21_30"
]

LATEX_REPLACEMENTS = [
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
]

def escape_latex(text: str) -> str:
    """Escapes common LaTeX special characters in user input."""
    for raw, esc in LATEX_REPLACEMENTS:
        text = re.sub(r"(?<!\\)" + re.escape(raw), esc, text)
    return text

def build_default_schedule() -> Dict[str, Dict[str, str]]:
    grid = {}
    for day in DEFAULT_AVAILABILITY_DAYS:
        grid[day] = {slot: "available" if "09_00" <= slot <= "17_00" else "busy" for slot in DEFAULT_SLOTS}
    return grid

def _fallback_generate_resume(template_path: Path, output_path: Path, profile: Dict[str, Any]) -> Path:
    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    placeholders = {
        "<<NAME>>": escape_latex(profile.get("name", "Candidate")),
        "<<LOCATION>>": escape_latex(profile.get("location", "City, Country")),
        "<<EMAIL>>": escape_latex(profile.get("email", "candidate@example.com")),
        "<<PHONE>>": escape_latex(profile.get("phone", "+1 555 0100")),
        "<<LINKEDIN>>": profile.get("linkedin", ""),
        "<<GITHUB>>": profile.get("github", ""),
        "<<SCHOOL>>": escape_latex(profile.get("school", "University")),
        "<<DEGREE>>": escape_latex(profile.get("degree", "B.S. in Computer Science / Data Science")),
        "<<GRADUATION>>": escape_latex(profile.get("graduation", "May 2027")),
    }
    
    rendered = template_content
    for tag, val in placeholders.items():
        rendered = rendered.replace(tag, str(val))
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    return output_path

def configure_vault(vault_dir: Path, profile: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    """Configures the vault preferences, Markdown sync, and starter LaTeX CV."""
    vault_dir = Path(vault_dir)
    bg_dir = vault_dir / "001-background"
    cv_dir = vault_dir / "002-cv"
    
    if dry_run:
        return {"success": True, "dry_run": True, "profile": profile}
        
    prefs_file = bg_dir / "preferences.json"
    existing_data = {}
    if prefs_file.exists():
        try:
            with open(prefs_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = {}
            
    candidate_data = {
        "name": profile.get("name", "Candidate"),
        "school": profile.get("school", "University"),
        "degree": profile.get("degree", "B.S. in Computer Science / Data Science"),
        "graduation": profile.get("graduation", "May 2027"),
        "location": profile.get("location", "City, Country"),
        "work_authorization": profile.get("work_authorization", "Needs Sponsorship / International"),
        "email": profile.get("email", "candidate@example.com"),
        "phone": profile.get("phone", "+1 555 0100"),
        "linkedin": profile.get("linkedin", "https://linkedin.com/in/username"),
        "github": profile.get("github", "https://github.com/username")
    }
    
    target_domains = profile.get("target_domains", ["Software Engineering", "Machine Learning", "Data Systems"])
    comp_floor = float(profile.get("minimum_hourly_usd", 20.0))
    
    prefs_payload = {
        "candidate": candidate_data,
        "modality": existing_data.get("modality", {
            "ranking": ["remote", "hybrid", "onsite"],
            "remote_preference": "highest"
        }),
        "schedule": existing_data.get("schedule", {
            "weekly_availability_grid": build_default_schedule(),
            "target_weekly_hours": 20,
            "max_weekly_hours": 30
        }),
        "compensation": {
            "minimum_hourly_usd": comp_floor,
            "currency": "USD"
        },
        "career_goals": {
            "target_domains": target_domains,
            "disallowed_industries": ["Crypto", "Gambling"]
        }
    }
    
    bg_dir.mkdir(parents=True, exist_ok=True)
    with open(prefs_file, "w", encoding="utf-8") as f:
        json.dump(prefs_payload, f, indent=2, ensure_ascii=False)
        
    # Attempt to sync preferences.md if preference_models is available
    try:
        pref_scripts = vault_dir / ".agents" / "skills" / "preference-manager" / "scripts"
        if pref_scripts.exists():
            if str(pref_scripts) not in sys.path:
                sys.path.insert(0, str(pref_scripts))
            import preference_models
            md_file = bg_dir / "preferences.md"
            preference_models.sync_to_markdown(prefs_payload, str(md_file))
    except Exception:
        pass

    # Generate starter resume if template exists
    template_tex = cv_dir / "template.tex"
    clean_name = candidate_data["name"].replace(" ", "_")
    output_tex = cv_dir / f"{clean_name}_Resume.tex"
    
    if template_tex.exists():
        if generate_resume_tex is not None:
            generate_resume_tex.generate_resume(template_tex, output_tex, candidate_data)
        else:
            _fallback_generate_resume(template_tex, output_tex, candidate_data)
        
    return {
        "success": True,
        "dry_run": False,
        "preferences_json": str(prefs_file),
        "resume_tex": str(output_tex) if output_tex.exists() else None
    }

def interactive_wizard() -> Dict[str, Any]:
    print("\n========================================================")
    print("  CAREER VAULT SETUP WIZARD (Data Science & SWE)        ")
    print("========================================================\n")
    name = input("Candidate Full Name: ").strip() or "Candidate"
    school = input("University / Institution: ").strip() or "University"
    degree = input("Degree / Major (e.g. B.S. in Data Science): ").strip() or "B.S. in Data Science"
    graduation = input("Expected Graduation (e.g. May 2027): ").strip() or "May 2027"
    location = input("Current Location (City, Country): ").strip() or "Querétaro, Mexico"
    visa = input("Work Authorization / Visa Status: ").strip() or "Needs Sponsorship"
    email = input("Contact Email: ").strip() or "candidate@example.com"
    phone = input("Contact Phone: ").strip() or "+1 555 0100"
    linkedin = input("LinkedIn URL: ").strip() or "https://linkedin.com"
    github = input("GitHub URL: ").strip() or "https://github.com"
    
    return {
        "name": name,
        "school": school,
        "degree": degree,
        "graduation": graduation,
        "location": location,
        "work_authorization": visa,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "target_domains": ["Software Engineering", "Machine Learning", "Data Platforms"]
    }

def main():
    parser = argparse.ArgumentParser(description="Career Vault Onboarding Wizard")
    parser.add_argument("--interactive", action="store_true", help="Run interactive prompt wizard")
    parser.add_argument("--json", help="Path to profile JSON input file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate configuration without writing files")
    args = parser.parse_args()
    
    vault_root = Path(__file__).resolve().parent
    
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            profile = json.load(f)
    elif args.interactive or len(sys.argv) == 1:
        profile = interactive_wizard()
    else:
        print("[INFO] Use --interactive or --json to configure vault. Exiting.")
        sys.exit(0)
        
    result = configure_vault(vault_root, profile, dry_run=args.dry_run)
    print("\n[SUCCESS] Vault configured successfully:")
    print(f"  - Preferences: {result.get('preferences_json')}")
    if result.get('resume_tex'):
        print(f"  - Starter LaTeX Resume: {result.get('resume_tex')}")

if __name__ == "__main__":
    main()

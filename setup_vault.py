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
import subprocess
import copy
from pathlib import Path
from typing import Dict, Any

# Ensure 002-cv/scripts is in path for dynamic resume templating
CV_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "002-cv", "scripts"))
if CV_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, CV_SCRIPTS_DIR)

# Ensure preference-manager scripts is in path
PREF_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".agents", "skills", "preference-manager", "scripts"))
if PREF_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, PREF_SCRIPTS_DIR)

try:
    import generate_resume_tex
except ImportError:
    generate_resume_tex = None

try:
    import preference_models
except ImportError:
    preference_models = None

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

def normalize_us_work_authorization(auth_str: Any) -> str:
    """Maps work authorization strings cleanly to canonical categories:
    - 'Citizen / Green Card'
    - 'TN Visa Eligible'
    - 'OPT/CPT Eligible'
    - 'None'
    """
    if not auth_str:
        return "None"
    s = str(auth_str).strip().lower()
    if any(k in s for k in ["citizen", "green card", "permanent resident", "pr"]):
        return "Citizen / Green Card"
    if any(k in s for k in ["tn visa", "tn-visa", "tn status", "usmca", "nafta"]) or s == "tn":
        return "TN Visa Eligible"
    if any(k in s for k in ["opt", "cpt", "f-1", "f1", "stem opt"]):
        return "OPT/CPT Eligible"
    return "None"

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
        "<<SCHOOL_LOCATION>>": escape_latex(profile.get("school_location", profile.get("location", "City, Country"))),
        "<<DEGREE>>": escape_latex(profile.get("degree", "B.S. in Computer Science / Data Science")),
        "<<GRADUATION>>": escape_latex(profile.get("graduation", "May 2027")),
        "<<GPA>>": escape_latex(profile.get("gpa", "3.9/4.0")),
        "<<DISTINCTIONS>>": escape_latex(profile.get("distinctions", "Dean's Honors List, Academic Excellence Scholarship")),
        "<<COURSEWORK>>": escape_latex(profile.get("coursework", "Distributed Systems, Machine Learning, Deep Learning, Algorithms & Data Structures, Database Systems, Computer Systems, Linear Algebra, Probability & Statistics")),
    }
    
    rendered = template_content
    for tag, val in placeholders.items():
        rendered = rendered.replace(tag, str(val))
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    return output_path

DEFAULT_PREFERENCES_FALLBACK = {
    "version": "1.1",
    "updated": "2026-10-02",
    "status": "active",
    "candidate": {
        "name": "Candidate",
        "university": "University",
        "school": "University",
        "degree": "B.S. in Computer Science / Data Science",
        "current_semester": "Junior",
        "expected_graduation": "May 2027",
        "location": "City, Country",
        "work_authorization": "Needs Sponsorship / International",
        "email_contact": "candidate@example.com",
        "email": "candidate@example.com",
        "phone": "+1 555 0100",
        "linkedin": "https://linkedin.com/in/username",
        "github": "https://github.com/username",
    },
    "metadata": {
        "created": "2026-10-02",
        "updated": "2026-10-02",
        "type": "preferences",
        "tags": ["background", "preferences", "constraints"],
        "status": "active",
        "version": "1.1",
        "source": "Career Vault Onboarding / Preference Manager",
        "privacy": "Configure with your personal preferences",
    },
    "academic_context": {
        "university": "University",
        "program": "B.S. in Computer Science / Data Science",
        "term": "Junior",
        "expected_graduation": "May 2027",
        "class_schedule_status": "Coursework in progress",
        "focus_areas": ["Machine Learning", "Software Engineering", "Data Systems"],
    },
    "availability_calendar": {
        "time_slots": [],
        "weekly_grid": {},
        "target_weekly_hours_min": 20,
        "target_weekly_hours_max": 30,
        "max_manageable_hours": 40,
        "schedule_notes": "Available weekday afternoons and evenings.",
    },
    "work_arrangement": {
        "preference_rank": ["Remote", "Hybrid", "Onsite"],
        "hours_per_week": "20-30 (40 manageable but not preferred)",
        "hours_flexibility": True,
        "timezone_overlap": "Flexible; prefers morning availability for classes",
        "communication_style": "Both async and sync acceptable",
        "scheduling_constraints": "Morning classes likely; schedule TBD",
    },
    "location_visa": {
        "current_location": "City, Country",
        "work_authorization": "Needs Sponsorship / International",
        "us_work_authorization": "None",
        "relocation_willingness": "Remote preferred; open to international relocation if visa sponsored",
        "travel_willingness": True,
    },
    "compensation_benefits": {
        "minimum_hourly": 20,
        "minimum_hourly_usd": 20,
        "equity_importance": "Don't care",
        "benefits_priorities": [
            "PTO",
            "Health insurance",
            "Learning budget",
            "Hardware stipend",
            "401k / Retirement plan",
        ],
        "negotiation_flexibility": "Flexible",
    },
    "industry_domain": {
        "target_industries": ["Any (no strong preference)"],
        "domains_of_interest": ["GenAI/LLMs", "RL", "Computer Vision", "NLP", "MLOps", "Research", "Applied ML"],
        "industries_to_avoid": ["Crypto"],
    },
    "learning_growth": {
        "mentorship": "Nice to have",
        "tech_depth_vs_breadth": "No preference",
        "conference_training_budget_expectation": "None",
        "career_trajectory": "Open",
        "skills_to_develop": ["Cloud ML", "LLM fine-tuning"],
    },
    "deal_breakers": {
        "hard_constraints": [
            "No onsite 5 days/week",
            "No unpaid overtime culture",
            "Must sponsor visa for relocation",
        ],
        "toxic_signals": ["Vague equity promises", "Hero culture"],
        "automatic_disqualifiers": [
            "Full-time only (no part-time/internship)",
            "Onsite required",
            "No remote option",
        ],
    },
    "role_responsibilities": {
        "ic_vs_lead": "IC preferred (not ready for lead)",
        "research_vs_engineering": "No preference",
        "team_size": "No preference",
    },
}

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

    # Initialize base payload from canonical schema
    if preference_models is not None and hasattr(preference_models, "DEFAULT_PREFERENCES"):
        canonical_base = copy.deepcopy(preference_models.DEFAULT_PREFERENCES)
    else:
        canonical_base = copy.deepcopy(DEFAULT_PREFERENCES_FALLBACK)
        canonical_base["availability_calendar"]["weekly_grid"] = build_default_schedule()

    prefs_payload = copy.deepcopy(canonical_base)

    # Preserve all existing data sections
    for k, v in existing_data.items():
        if k in prefs_payload and isinstance(prefs_payload[k], dict):
            if isinstance(v, dict):
                prefs_payload[k].update(v)
        elif v is not None:
            prefs_payload[k] = v

    # Extract candidate values from profile with fallbacks
    cand = prefs_payload.get("candidate") or {}

    def _safe_str(val: Any, fallback: str = "") -> str:
        if val is None:
            return fallback
        s = str(val).strip()
        return s if s else fallback

    name = _safe_str(profile.get("name")) or cand.get("name") or "Candidate"
    school = _safe_str(profile.get("school")) or _safe_str(profile.get("university")) or cand.get("school") or cand.get("university") or "University"
    degree = _safe_str(profile.get("degree")) or _safe_str(profile.get("program")) or cand.get("degree") or "B.S. in Computer Science / Data Science"
    graduation = _safe_str(profile.get("graduation")) or _safe_str(profile.get("expected_graduation")) or cand.get("graduation") or "May 2027"
    current_semester = _safe_str(profile.get("current_semester")) or _safe_str(profile.get("term")) or cand.get("current_semester") or "Junior"
    location = _safe_str(profile.get("location")) or cand.get("location") or "City, Country"
    work_auth = _safe_str(profile.get("work_authorization")) or cand.get("work_authorization") or "Needs Sponsorship / International"
    email = _safe_str(profile.get("email")) or _safe_str(profile.get("email_contact")) or cand.get("email") or "candidate@example.com"
    phone = _safe_str(profile.get("phone")) or cand.get("phone") or "+1 555 0100"
    linkedin = _safe_str(profile.get("linkedin")) or cand.get("linkedin") or "https://linkedin.com/in/username"
    github = _safe_str(profile.get("github")) or cand.get("github") or "https://github.com/username"

    # Robust handling of target_domains: ensure it is a list, not None
    default_domains = (prefs_payload.get("industry_domain") or {}).get(
        "domains_of_interest", ["Software Engineering", "Machine Learning", "Data Systems"]
    )
    if not isinstance(default_domains, list) or not default_domains:
        default_domains = ["Software Engineering", "Machine Learning", "Data Systems"]

    raw_domains = profile.get("target_domains") if "target_domains" in profile else None
    if raw_domains is not None:
        if isinstance(raw_domains, list):
            target_domains = [str(d).strip() for d in raw_domains if d is not None and str(d).strip()]
            if not target_domains:
                target_domains = list(default_domains)
        elif isinstance(raw_domains, str) and raw_domains.strip():
            target_domains = [d.strip() for d in raw_domains.split(",") if d.strip()]
        else:
            target_domains = list(default_domains)
    else:
        target_domains = list(default_domains)

    # Robust parsing of comp_floor with try/except fallback to 20.0
    raw_comp = None
    if profile.get("minimum_hourly_usd") is not None and str(profile.get("minimum_hourly_usd")).strip() != "":
        raw_comp = profile.get("minimum_hourly_usd")
    elif profile.get("minimum_hourly") is not None and str(profile.get("minimum_hourly")).strip() != "":
        raw_comp = profile.get("minimum_hourly")
    else:
        raw_comp = (prefs_payload.get("compensation_benefits") or {}).get("minimum_hourly", 20.0)

    try:
        comp_floor = float(raw_comp)
    except (ValueError, TypeError):
        comp_floor = 20.0

    # Update candidate section
    candidate_data = dict(cand)
    candidate_data.update({
        "name": name,
        "school": school,
        "university": school,
        "degree": degree,
        "graduation": graduation,
        "expected_graduation": graduation,
        "current_semester": current_semester,
        "location": location,
        "work_authorization": work_auth,
        "email": email,
        "email_contact": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
    })
    prefs_payload["candidate"] = candidate_data

    # Update academic_context
    acad = prefs_payload.get("academic_context") or {}
    acad["university"] = school
    acad["program"] = degree
    acad["term"] = current_semester
    acad["expected_graduation"] = graduation
    if "target_domains" in profile:
        acad["focus_areas"] = target_domains
    elif "focus_areas" not in acad or not isinstance(acad.get("focus_areas"), list):
        acad["focus_areas"] = target_domains
    prefs_payload["academic_context"] = acad

    # Update location_visa
    loc_v = prefs_payload.get("location_visa") or {}
    loc_v["current_location"] = location
    loc_v["work_authorization"] = work_auth
    target_auth = profile.get("us_work_authorization") or profile.get("work_authorization")
    if target_auth:
        norm_auth = normalize_us_work_authorization(target_auth)
        if norm_auth != "None" or loc_v.get("us_work_authorization") in [None, "", "None"]:
            loc_v["us_work_authorization"] = norm_auth
    elif not loc_v.get("us_work_authorization") or loc_v.get("us_work_authorization") == "None":
        loc_v["us_work_authorization"] = normalize_us_work_authorization(work_auth)
    prefs_payload["location_visa"] = loc_v

    # Update compensation_benefits
    comp_b = prefs_payload.get("compensation_benefits") or {}
    comp_b["minimum_hourly"] = comp_floor
    comp_b["minimum_hourly_usd"] = comp_floor
    prefs_payload["compensation_benefits"] = comp_b

    # Update industry_domain
    ind = prefs_payload.get("industry_domain") or {}
    if "target_domains" in profile:
        ind["domains_of_interest"] = target_domains
    elif "domains_of_interest" not in ind or not isinstance(ind.get("domains_of_interest"), list):
        ind["domains_of_interest"] = target_domains
    prefs_payload["industry_domain"] = ind

    # Backward-compatible top-level keys
    if "modality" in existing_data and isinstance(existing_data["modality"], dict):
        prefs_payload["modality"] = existing_data["modality"]
    else:
        prefs_payload["modality"] = {
            "ranking": ["remote", "hybrid", "onsite"],
            "remote_preference": "highest"
        }

    if "schedule" in existing_data and isinstance(existing_data["schedule"], dict):
        prefs_payload["schedule"] = existing_data["schedule"]
    else:
        prefs_payload["schedule"] = {
            "weekly_availability_grid": (prefs_payload.get("availability_calendar") or {}).get("weekly_grid", build_default_schedule()),
            "target_weekly_hours": (prefs_payload.get("availability_calendar") or {}).get("target_weekly_hours_min", 20),
            "max_weekly_hours": (prefs_payload.get("availability_calendar") or {}).get("target_weekly_hours_max", 30)
        }

    if "compensation" in existing_data and isinstance(existing_data["compensation"], dict):
        prefs_payload["compensation"] = dict(existing_data["compensation"])
        prefs_payload["compensation"]["minimum_hourly_usd"] = comp_floor
    else:
        prefs_payload["compensation"] = {
            "minimum_hourly_usd": comp_floor,
            "currency": "USD"
        }

    if "career_goals" in existing_data and isinstance(existing_data["career_goals"], dict):
        prefs_payload["career_goals"] = dict(existing_data["career_goals"])
        if "target_domains" in profile:
            prefs_payload["career_goals"]["target_domains"] = target_domains
    else:
        prefs_payload["career_goals"] = {
            "target_domains": target_domains,
            "disallowed_industries": ["Crypto", "Gambling"]
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
            import preference_models as pm
            md_file = bg_dir / "preferences.md"
            pm.sync_to_markdown(prefs_payload, str(md_file))
        elif preference_models is not None:
            md_file = bg_dir / "preferences.md"
            preference_models.sync_to_markdown(prefs_payload, str(md_file))
    except Exception:
        pass

    # Generate starter resume if template exists
    template_tex = cv_dir / "template.tex"
    clean_name = (candidate_data.get("name") or "Candidate").strip().replace(" ", "_") or "Candidate"
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
    print("========================================================")
    print("Please answer the following prompts to personalize your vault.")
    print("Expected formats and examples are shown for each field.")
    print("Press [Enter] to keep the default value shown in brackets.\n")
    
    name = input("1. Full Name (e.g. Alex Rivera) [Candidate]: ").strip() or "Candidate"
    school = input("2. University / Institution (e.g. Stanford University, MIT, UNAM) [University]: ").strip() or "University"
    degree = input("3. Degree & Major (e.g. B.S. in Computer Science / Data Science) [B.S. in Data Science]: ").strip() or "B.S. in Data Science"
    graduation = input("4. Expected Graduation Term (e.g. May 2027, December 2026) [May 2027]: ").strip() or "May 2027"
    location = input("5. Current Location [City, Country/State] (e.g. Austin, TX, USA or Berlin, Germany) [City, Country]: ").strip() or "City, Country"
    visa = input("6. Work Authorization / Visa Status (e.g. US Citizen, F-1 OPT/CPT, Needs Sponsorship) [Needs Sponsorship]: ").strip() or "Needs Sponsorship"
    email = input("7. Professional Email (e.g. alex.rivera@example.com) [candidate@example.com]: ").strip() or "candidate@example.com"
    phone = input("8. Contact Phone [with country code] (e.g. +1 555 0100 or +44 20 7946 0919) [+1 555 0100]: ").strip() or "+1 555 0100"
    linkedin = input("9. LinkedIn Profile URL (e.g. https://linkedin.com/in/alex-rivera) [https://linkedin.com]: ").strip() or "https://linkedin.com"
    github = input("10. GitHub Profile URL (e.g. https://github.com/alexrivera) [https://github.com]: ").strip() or "https://github.com"
    
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

def launch_preferences_server(vault_root: Path, open_browser: bool = True) -> bool:
    """Launches the Preference Manager web server and opens the browser UI."""
    pref_server_script = vault_root / ".agents" / "skills" / "preference-manager" / "scripts" / "preference_server.py"
    if not pref_server_script.exists():
        print(f"[WARN] Preference server script not found at {pref_server_script}")
        return False

    venv_dir = vault_root / ".venv"
    py_bin, _ = get_venv_executables(venv_dir)
    python_exec = str(py_bin) if py_bin.exists() else sys.executable

    print("\n========================================================")
    print("  LAUNCHING PREFERENCES MANAGER WEB PORTAL               ")
    print("========================================================")
    print("Opening interactive preferences portal in your browser...")
    print("You can configure your weekly availability schedule, hourly wage,")
    print("work modalities (remote/hybrid/onsite), and location constraints.")
    print("In the browser portal, click 'Save & Quit' to save and continue setup,")
    print("or click 'Save Preferences' to keep testing. Press Ctrl+C anytime to exit.\n")

    cmd = [python_exec, str(pref_server_script)]
    if open_browser:
        cmd.append("--open")

    try:
        subprocess.run(cmd)
        return True
    except KeyboardInterrupt:
        print("\n[INFO] Preferences Manager closed.")
        return True
    except Exception as e:
        print(f"[WARN] Could not launch preferences server: {e}")
        return False

RECOMMENDED_PACKAGES = ["pdfplumber", "pypdfium2", "pytest"]

def check_missing_dependencies() -> list:
    """Checks which recommended third-party packages are missing from the current Python environment."""
    missing = []
    for pkg in RECOMMENDED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing

def get_venv_executables(venv_dir: Path) -> tuple:
    """Returns the (python_path, pip_path) for a virtual environment across Windows and POSIX."""
    if os.name == "nt":
        py_bin = venv_dir / "Scripts" / "python.exe"
        pip_bin = venv_dir / "Scripts" / "pip.exe"
    else:
        py_bin = venv_dir / "bin" / "python"
        pip_bin = venv_dir / "bin" / "pip"
    return py_bin, pip_bin

def auto_setup_environment(vault_root: Path) -> bool:
    """
    Creates a .venv if not present, and installs dependencies from requirements.txt.
    Returns True if successfully installed.
    """
    venv_dir = vault_root / ".venv"
    req_file = vault_root / "requirements.txt"
    
    print("\n--------------------------------------------------------")
    print("  SETTING UP VIRTUAL ENVIRONMENT & DEPENDENCIES         ")
    print("--------------------------------------------------------")
    
    in_venv = (sys.prefix != sys.base_prefix)
    
    if in_venv:
        print("[INFO] Already running inside an active virtual environment.")
        pip_cmd = [sys.executable, "-m", "pip", "install"]
    else:
        if not venv_dir.exists():
            print(f"[1/2] Creating virtual environment at {venv_dir.name}...")
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
                print("      Virtual environment (.venv) created successfully.")
            except Exception as e:
                print(f"[ERROR] Failed to create virtual environment: {e}", file=sys.stderr)
                return False
        else:
            print(f"[INFO] Existing virtual environment found at {venv_dir.name}.")
            
        py_bin, pip_bin = get_venv_executables(venv_dir)
        if not py_bin.exists():
            print(f"[ERROR] Python binary not found at {py_bin}", file=sys.stderr)
            return False
        pip_cmd = [str(py_bin), "-m", "pip", "install"]

    print("[2/2] Installing requirements from requirements.txt...")
    try:
        if req_file.exists():
            subprocess.run(pip_cmd + ["-r", str(req_file)], check=True)
        else:
            subprocess.run(pip_cmd + RECOMMENDED_PACKAGES, check=True)
        print("\n[SUCCESS] Dependencies installed successfully!")
        if not in_venv:
            if os.name == "nt":
                print("  To activate in PowerShell: .\\.venv\\Scripts\\Activate.ps1")
                print("  To activate in CMD:        .\\.venv\\Scripts\\activate.bat")
            else:
                print("  To activate in terminal:   source .venv/bin/activate")
        print("--------------------------------------------------------\n")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to install dependencies via pip: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Career Vault Onboarding Wizard")
    parser.add_argument("--interactive", action="store_true", help="Run interactive prompt wizard")
    parser.add_argument("--json", help="Path to profile JSON input file")
    parser.add_argument("--dry-run", action="store_true", help="Simulate configuration without writing files")
    parser.add_argument("--install-deps", action="store_true", help="Automatically create .venv and install dependencies")
    parser.add_argument("--skip-deps", action="store_true", help="Skip checking or installing dependencies")
    parser.add_argument("--skip-prefs", action="store_true", help="Skip launching the preference manager web portal")
    args = parser.parse_args()
    
    vault_root = Path(__file__).resolve().parent
    
    # Auto-dependency setup check
    if args.install_deps:
        auto_setup_environment(vault_root)
    elif not args.skip_deps and (args.interactive or len(sys.argv) == 1):
        missing = check_missing_dependencies()
        if missing:
            print(f"\n[INFO] Missing recommended Python dependencies: {', '.join(missing)}")
            try:
                ans = input("Would you like to auto-create a virtual environment (.venv) and install dependencies? [Y/n]: ").strip().lower()
                if ans not in ["n", "no"]:
                    auto_setup_environment(vault_root)
            except (EOFError, KeyboardInterrupt):
                pass
    
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

    if not args.dry_run and not args.skip_prefs:
        launch_preferences_server(vault_root, open_browser=True)

    if not args.dry_run:
        print("\n" + "=" * 65)
        print(" CAREER VAULT SETUP COMPLETE!")
        print("=" * 65)
        print("\nNEXT STEP:")
        print("Open this folder in your AI harness (Google Antigravity, Claude Code,")
        print("Cursor Agent, OpenCode, etc.) and send your agent this kickoff prompt:\n")
        print("  Hi, I already ran the setup script, what is the next step?\n")
        print("Your agent will inspect your profile, verify your starter resume,")
        print("and guide your career search across the 11 vault skills.")
        print("=" * 65 + "\n")

if __name__ == "__main__":
    main()

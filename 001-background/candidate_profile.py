#!/usr/bin/env python3
"""
Dynamic Candidate Profile Loader.
Extracts candidate information, university background, contact links,
and career target domains from preferences.json with safe defaults for DS & SWE profiles.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union

DEFAULT_PROFILE = {
    "name": "Candidate",
    "school": "University",
    "degree": "B.S. in Computer Science / Data Science",
    "graduation": "Expected May 2027",
    "location": "City, Country",
    "work_authorization": "Needs Sponsorship / International",
    "email": "candidate@example.com",
    "phone": "+1 555 0100",
    "linkedin": "https://linkedin.com/in/username",
    "github": "https://github.com/username",
    "target_domains": ["Software Engineering", "Machine Learning", "Data Systems"],
    "compensation_floor": 20.0
}


def load_profile(preferences_path: Union[str, Path, None] = None) -> Dict[str, Any]:
    """Loads candidate profile from preferences.json with sensible fallbacks."""
    if preferences_path is None:
        preferences_path = Path(__file__).resolve().parent / "preferences.json"
    else:
        preferences_path = Path(preferences_path)
        
    if not preferences_path.exists():
        return dict(DEFAULT_PROFILE)
        
    try:
        with open(preferences_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(DEFAULT_PROFILE)
    except Exception:
        return dict(DEFAULT_PROFILE)
        
    cand = data.get("candidate", {}) if isinstance(data.get("candidate"), dict) else {}
    acad = data.get("academic_context", {}) if isinstance(data.get("academic_context"), dict) else {}
    goals = data.get("career_goals", {}) if isinstance(data.get("career_goals"), dict) else {}
    industry = data.get("industry_domain", {}) if isinstance(data.get("industry_domain"), dict) else {}
    comp_canonical = data.get("compensation_benefits", {}) if isinstance(data.get("compensation_benefits"), dict) else {}
    comp_legacy = data.get("compensation", {}) if isinstance(data.get("compensation"), dict) else {}
    loc_visa = data.get("location_visa", {}) if isinstance(data.get("location_visa"), dict) else {}
    
    # Prioritize canonical compensation_benefits over legacy compensation
    comp_val = (
        comp_canonical.get("minimum_hourly")
        if comp_canonical.get("minimum_hourly") is not None
        else (
            comp_canonical.get("minimum_hourly_usd")
            if comp_canonical.get("minimum_hourly_usd") is not None
            else (
                comp_legacy.get("minimum_hourly_usd")
                if comp_legacy.get("minimum_hourly_usd") is not None
                else (
                    comp_legacy.get("minimum_hourly")
                    if comp_legacy.get("minimum_hourly") is not None
                    else comp_legacy.get("floor")
                )
            )
        )
    )
    if comp_val is None:
        comp_val = DEFAULT_PROFILE["compensation_floor"]
    try:
        compensation_floor = float(comp_val)
    except (ValueError, TypeError):
        compensation_floor = DEFAULT_PROFILE["compensation_floor"]

    school = (
        cand.get("school")
        or cand.get("university")
        or acad.get("university")
        or DEFAULT_PROFILE["school"]
    )
    degree = (
        cand.get("degree")
        or cand.get("major")
        or acad.get("program")
        or DEFAULT_PROFILE["degree"]
    )
    graduation = (
        cand.get("graduation")
        or cand.get("expected_graduation")
        or acad.get("expected_graduation")
        or DEFAULT_PROFILE["graduation"]
    )
    location = (
        cand.get("location")
        or loc_visa.get("current_location")
        or DEFAULT_PROFILE["location"]
    )

    raw_us_auth = str(loc_visa.get("us_work_authorization", "")).strip()
    valid_us_auth = raw_us_auth if raw_us_auth and raw_us_auth.lower() not in ["none", "no"] else None

    work_auth = (
        cand.get("work_authorization")
        or loc_visa.get("work_authorization")
        or valid_us_auth
        or DEFAULT_PROFILE["work_authorization"]
    )

    target_domains = (
        industry.get("domains_of_interest")
        or goals.get("target_domains")
        or DEFAULT_PROFILE["target_domains"]
    )
    if not isinstance(target_domains, list):
        target_domains = DEFAULT_PROFILE["target_domains"]

    profile = {
        "name": cand.get("name") or DEFAULT_PROFILE["name"],
        "school": school,
        "university": school,
        "degree": degree,
        "major": degree,
        "graduation": graduation,
        "expected_graduation": graduation,
        "location": location,
        "current_location": location,
        "work_authorization": work_auth,
        "email": cand.get("email") or cand.get("email_contact") or DEFAULT_PROFILE["email"],
        "phone": cand.get("phone") or DEFAULT_PROFILE["phone"],
        "linkedin": cand.get("linkedin") or DEFAULT_PROFILE["linkedin"],
        "github": cand.get("github") or DEFAULT_PROFILE["github"],
        "target_domains": target_domains,
        "compensation_floor": compensation_floor
    }
    return profile


if __name__ == "__main__":
    import pprint
    pprint.pprint(load_profile())


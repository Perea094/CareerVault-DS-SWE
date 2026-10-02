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
    goals = data.get("career_goals", {}) if isinstance(data.get("career_goals"), dict) else {}
    comp = data.get("compensation", {}) if isinstance(data.get("compensation"), dict) else (
        data.get("compensation_benefits", {}) if isinstance(data.get("compensation_benefits"), dict) else {}
    )
    loc_visa = data.get("location_visa", {}) if isinstance(data.get("location_visa"), dict) else {}
    industry = data.get("industry_domain", {}) if isinstance(data.get("industry_domain"), dict) else {}
    
    compensation_floor = (
        comp.get("minimum_hourly_usd")
        or comp.get("minimum_hourly")
        or DEFAULT_PROFILE["compensation_floor"]
    )
    try:
        compensation_floor = float(compensation_floor)
    except (ValueError, TypeError):
        compensation_floor = DEFAULT_PROFILE["compensation_floor"]

    profile = {
        "name": cand.get("name") or DEFAULT_PROFILE["name"],
        "school": cand.get("school") or cand.get("university") or DEFAULT_PROFILE["school"],
        "degree": cand.get("degree") or DEFAULT_PROFILE["degree"],
        "graduation": cand.get("graduation") or cand.get("expected_graduation") or DEFAULT_PROFILE["graduation"],
        "location": cand.get("location") or loc_visa.get("current_location") or DEFAULT_PROFILE["location"],
        "work_authorization": cand.get("work_authorization") or loc_visa.get("us_work_authorization") or DEFAULT_PROFILE["work_authorization"],
        "email": cand.get("email") or cand.get("email_contact") or DEFAULT_PROFILE["email"],
        "phone": cand.get("phone") or DEFAULT_PROFILE["phone"],
        "linkedin": cand.get("linkedin") or DEFAULT_PROFILE["linkedin"],
        "github": cand.get("github") or DEFAULT_PROFILE["github"],
        "target_domains": goals.get("target_domains") or industry.get("domains_of_interest") or DEFAULT_PROFILE["target_domains"],
        "compensation_floor": compensation_floor
    }
    return profile


if __name__ == "__main__":
    import pprint
    pprint.pprint(load_profile())

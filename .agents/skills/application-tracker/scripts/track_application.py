#!/usr/bin/env python3
"""
Application Pipeline Tracker.
Manages application lifecycle progression (wishlist -> applied -> oa_received -> screening -> interview -> offer -> rejected -> withdrawn),
updates opportunities.json, and generates Obsidian Dataview/Kanban dashboards.
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Union

VALID_STATUSES = [
    "wishlist",
    "applied",
    "oa_received",
    "screening",
    "interview",
    "offer",
    "rejected",
    "withdrawn"
]

def load_database(path: Union[str, Path]) -> Dict[str, Any]:
    """Loads database from JSON file."""
    path = Path(path)
    if not path.exists():
        return {"opportunities": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_database(
    data: Dict[str, Any],
    primary_path: Union[str, Path],
    mirror_path: Union[str, Path] = None,
    csv_path: Union[str, Path] = None
):
    """Saves database to primary JSON, optional mirror JSON, and CSV."""
    primary_path = Path(primary_path)
    primary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(primary_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    if mirror_path:
        mirror_path = Path(mirror_path)
        mirror_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mirror_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    if csv_path:
        csv_path = Path(csv_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        opps = data.get("opportunities", [])
        if opps:
            fieldnames = list(opps[0].keys())
        else:
            fieldnames = ["id", "company", "role", "pipeline_status", "date_applied", "notes"]
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for opp in opps:
                writer.writerow(opp)

def update_opportunity_pipeline(
    db: Dict[str, Any],
    opp_id: str,
    new_status: str,
    date_applied: str = None,
    notes: str = None
) -> Dict[str, Any]:
    """Updates the pipeline status and metadata for a specific opportunity."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: '{new_status}'. Must be one of {VALID_STATUSES}")
        
    found = False
    for opp in db.get("opportunities", []):
        if opp.get("id") == opp_id or opp.get("company", "").lower() == opp_id.lower():
            opp["pipeline_status"] = new_status
            if date_applied:
                opp["date_applied"] = date_applied
            if notes:
                opp["pipeline_notes"] = notes
            found = True
            break
            
    if not found:
        raise ValueError(f"Opportunity with ID or Company '{opp_id}' not found in database.")
        
    return db

def generate_pipeline_dashboard(opportunities: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
    """Generates an Obsidian Kanban and summary dashboard."""
    if isinstance(opportunities, dict):
        opp_list = opportunities.get("opportunities", [])
    else:
        opp_list = opportunities
        
    grouped: Dict[str, List[Dict[str, Any]]] = {status: [] for status in VALID_STATUSES}
    
    for opp in opp_list:
        st = opp.get("pipeline_status", "wishlist")
        if st in grouped:
            grouped[st].append(opp)
        else:
            grouped["wishlist"].append(opp)
            
    today_str = datetime.now().strftime("%Y-%m-%d")
    md = f"""---
created: {today_str}
type: pipeline-dashboard
tags: [pipeline, kanban, applications]
---

# Application Pipeline Dashboard

"""
    for status in VALID_STATUSES:
        title = status.replace("_", " ").title()
        md += f"## {title}\n"
        items = grouped[status]
        if not items:
            md += "- *No applications in this stage*\n\n"
        else:
            for item in items:
                comp = item.get("company", "Unknown")
                role = item.get("role", "Unknown")
                url = item.get("apply_url", "#")
                date = item.get("date_applied", "")
                date_str = f" | Applied: {date}" if date else ""
                md += f"- [ ] **[{comp}]({url})** — {role}{date_str}\n"
            md += "\n"
            
    return md

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Application Pipeline Tracker")
    parser.add_argument("--db", default="004-work-opportunities/database/opportunities.json", help="Path to opportunities.json")
    parser.add_argument("--dashboard", action="store_true", help="Generate application pipeline dashboard markdown")
    parser.add_argument("--output", default="004-work-opportunities/application-pipeline.md", help="Output path for dashboard")
    parser.add_argument("--update", action="store_true", help="Update opportunity status")
    parser.add_argument("--id", help="Opportunity ID or company name")
    parser.add_argument("--status", choices=VALID_STATUSES, help="New pipeline status")
    parser.add_argument("--date", help="Application date (YYYY-MM-DD)")
    parser.add_argument("--notes", help="Application notes")
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.dashboard:
        db = load_database(db_path)
        md = generate_pipeline_dashboard(db)
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[OK] Generated dashboard at {out_path}")
    elif args.update:
        if not args.id or not args.status:
            print("Error: --update requires --id and --status", file=sys.stderr)
            sys.exit(1)
        db = load_database(db_path)
        update_opportunity_pipeline(db, args.id, args.status, date_applied=args.date, notes=args.notes)
        save_database(db, db_path, mirror_path="004-work-opportunities/opportunities-database.json", csv_path="004-work-opportunities/database/opportunities.csv")
        print(f"[OK] Updated '{args.id}' to '{args.status}'")

if __name__ == "__main__":
    main()

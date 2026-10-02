import os
import sys
import json
import csv
import argparse
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database", "opportunities.json")
MIRROR_PATH = os.path.join(BASE_DIR, "opportunities-database.json")
CSV_PATH = os.path.join(BASE_DIR, "database", "opportunities.csv")
ARCHIVE_PATH = os.path.join(BASE_DIR, "database", "archived_opportunities.json")

CSV_FIELDS = [
    "ID", "Numeric_ID", "Company", "Role", "Tier", "Location", "Work_Arrangement",
    "Hours_Per_Week", "Compensation", "Realistic_Success_Ratio", "Urgency",
    "Strategic_Action", "Status", "Application_Status", "Apply_URL", "Vault_Note",
    "Key_Highlights_Summary", "Missing_Skills_Summary"
]

CLOSED_KEYWORDS = [
    "no longer accepting applications",
    "this job is no longer available",
    "this posting has closed",
    "position has been filled",
    "requisition closed",
    "this job has been unlisted",
    "job not found",
    "the role you are looking for is no longer active",
    "job expired",
    "this vacancy has expired"
]

def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Error reading {path}: {e}", file=sys.stderr)
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def sync_csv(opportunities):
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        for o in opportunities:
            writer.writerow({
                "ID": o.get("id", ""),
                "Numeric_ID": o.get("numeric_id", ""),
                "Company": o.get("company", ""),
                "Role": o.get("role", ""),
                "Tier": o.get("tier", ""),
                "Location": o.get("location", ""),
                "Work_Arrangement": o.get("work_arrangement", ""),
                "Hours_Per_Week": o.get("hours_per_week", ""),
                "Compensation": o.get("compensation", ""),
                "Realistic_Success_Ratio": o.get("realistic_success_ratio", ""),
                "Urgency": o.get("urgency", ""),
                "Strategic_Action": o.get("strategic_action", ""),
                "Status": o.get("status", ""),
                "Application_Status": o.get("application_status", ""),
                "Apply_URL": o.get("apply_url", ""),
                "Vault_Note": o.get("vault_note", ""),
                "Key_Highlights_Summary": " | ".join(o.get("key_points_to_highlight", []) or []),
                "Missing_Skills_Summary": " | ".join(o.get("missing_or_bridge_skills", []) or [])
            })

def check_single_link(opp):
    url = opp.get("apply_url")
    if not url:
        return opp, False, "Missing URL"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            # Read first 16KB of response
            content = resp.read(16384).decode("utf-8", errors="ignore").lower()
            for kw in CLOSED_KEYWORDS:
                if kw in content:
                    return opp, False, f"ATS Closed Message: '{kw}'"
            return opp, True, "Active (200 OK)"
    except urllib.error.HTTPError as e:
        if e.code in [404, 410]:
            return opp, False, f"Dead Link (HTTP {e.code})"
        elif e.code in [401, 403]:
            # Often protected ATS or Cloudflare, assume alive
            return opp, True, f"Protected ATS (HTTP {e.code})"
        return opp, False, f"HTTP Error {e.code}"
    except Exception as e:
        # Timeout or network error, assume alive to avoid accidental deletion
        return opp, True, f"Network timeout/skip: {e}"

def parse_iso_or_date(d_str):
    if not d_str:
        return None
    try:
        return datetime.fromisoformat(d_str.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.strptime(d_str, "%Y-%m-%d")
        except Exception:
            return None

def main():
    parser = argparse.ArgumentParser(description="Prune and archive finished, dead, or passed opportunities.")
    parser.add_argument("--check-links", action="store_true", help="Probe apply_url to identify 404s and closed ATS requisitions.")
    parser.add_argument("--older-than", type=int, default=None, help="Archive opportunities older than N days without active status.")
    parser.add_argument("--archive-status", type=str, default=None, help="Comma-separated statuses to archive (e.g. 'passed,rejected,closed,expired').")
    parser.add_argument("--id", type=str, default=None, help="Specific opportunity ID or numeric ID to archive.")
    parser.add_argument("--mark-passed", type=str, default=None, help="Shortcut: mark specific ID as 'passed' and archive immediately.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate pruning without modifying database files.")
    parser.add_argument("--list-archived", action="store_true", help="List all currently archived opportunities and exit.")
    args = parser.parse_args()

    # 1. Handle --list-archived
    if args.list_archived:
        archive_data = load_json(ARCHIVE_PATH, {"opportunities": []})
        archived = archive_data.get("opportunities", [])
        print(f"\n================ ARCHIVED REGISTRY ({len(archived)} records) ================")
        for idx, a in enumerate(archived, 1):
            print(f"{idx}. [{a.get('archive_reason', 'N/A')}] {a.get('company')} - {a.get('role')}")
            print(f"   Archived Date: {a.get('archived_date', 'N/A')} | Original Status: {a.get('original_application_status', 'N/A')}")
            print(f"   Link: {a.get('apply_url')}\n")
        return

    # 2. Load active database
    db = load_json(DB_PATH)
    if not db or "opportunities" not in db:
        print(f"[ERROR] Could not load active database from {DB_PATH}", file=sys.stderr)
        return

    active_opps = db.get("opportunities", [])
    print(f"Loaded active database: {len(active_opps)} opportunities.")

    now = datetime.now()
    to_archive = []  # list of tuples: (opp, reason)
    keep_opps = []

    status_filter = [s.strip().lower() for s in args.archive_status.split(",")] if args.archive_status else []

    # Handle shortcut --mark-passed
    if args.mark_passed:
        target_id = str(args.mark_passed).strip().lower()
        for o in active_opps:
            oid = str(o.get("id", "")).lower()
            num_id = str(o.get("numeric_id", "")).lower()
            if oid == target_id or num_id == target_id:
                to_archive.append((o, "Manually marked as 'passed'"))
            else:
                keep_opps.append(o)
    else:
        # Check links if requested
        link_results = {}
        if args.check_links:
            print(f"Probing {len(active_opps)} opportunity links via concurrent workers...")
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(check_single_link, o) for o in active_opps]
                for f in futures:
                    opp, is_live, reason = f.result()
                    link_results[opp.get("id")] = (is_live, reason)
                    if not is_live:
                        print(f"  [CLOSED] {opp.get('company')} - {opp.get('role')}: {reason}")

        for o in active_opps:
            oid = o.get("id")
            num_id = str(o.get("numeric_id", ""))
            reasons = []

            # Filter by ID
            if args.id and (oid == args.id or num_id == args.id):
                reasons.append(f"Explicit ID match: {args.id}")

            # Filter by link check
            if args.check_links and oid in link_results:
                is_live, link_reason = link_results[oid]
                if not is_live:
                    reasons.append(link_reason)

            # Filter by status
            app_status = str(o.get("application_status", "")).lower()
            vault_status = str(o.get("status", "")).lower()
            if status_filter:
                if app_status in status_filter or vault_status in status_filter:
                    reasons.append(f"Matching status: '{app_status}'")

            # Filter by age
            if args.older_than is not None:
                # Do not prune if currently interviewing or offered
                if app_status not in ["interviewing", "offer", "applied"]:
                    date_ref = parse_iso_or_date(o.get("last_audited") or o.get("date_identified"))
                    if date_ref:
                        age_days = (now - date_ref).days
                        if age_days > args.older_than:
                            reasons.append(f"Stale ({age_days}d > {args.older_than}d threshold)")

            if reasons:
                to_archive.append((o, "; ".join(reasons)))
            else:
                keep_opps.append(o)

    # 3. Report findings
    print(f"\n================ PRUNING EVALUATION ================")
    print(f"Active opportunities kept: {len(keep_opps)}")
    print(f"Opportunities to archive: {len(to_archive)}")
    for idx, (o, reason) in enumerate(to_archive, 1):
        print(f"  {idx}. [{reason}] {o.get('company')} - {o.get('role')}")

    if not to_archive:
        print("\nNo opportunities flagged for archival. Database is up to date!")
        return

    if args.dry_run:
        print("\n[DRY RUN] No changes were written to disk. Run without --dry-run to commit.")
        return

    # 4. Commit to Archive
    archive_data = load_json(ARCHIVE_PATH, {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Career Vault Archived Opportunities Registry",
        "description": "Archived, closed, expired, or passed opportunities retained for deduplication and audit history.",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "total_archived": 0,
        "opportunities": []
    })

    archived_list = archive_data.get("opportunities", [])
    today_str = datetime.now().strftime("%Y-%m-%d")

    for o, reason in to_archive:
        o_copy = dict(o)
        o_copy["original_application_status"] = o.get("application_status", "pending_tailoring")
        o_copy["status"] = "archived"
        o_copy["application_status"] = "closed"
        o_copy["archived_date"] = today_str
        o_copy["archive_reason"] = reason
        archived_list.append(o_copy)

    archive_data["opportunities"] = archived_list
    archive_data["total_archived"] = len(archived_list)
    archive_data["last_updated"] = today_str

    save_json(ARCHIVE_PATH, archive_data)
    print(f"\n[OK] Archived {len(to_archive)} records -> {ARCHIVE_PATH}")

    # 5. Commit to Active Database & Mirror
    db["opportunities"] = keep_opps
    db["total_records"] = len(keep_opps)
    db["last_updated"] = today_str

    save_json(DB_PATH, db)
    save_json(MIRROR_PATH, db)
    print(f"[OK] Updated active database ({len(keep_opps)} active records) -> {DB_PATH}")

    # 6. Synchronize CSV
    sync_csv(keep_opps)
    print(f"[OK] Synchronized CSV -> {CSV_PATH}\n")

if __name__ == "__main__":
    main()

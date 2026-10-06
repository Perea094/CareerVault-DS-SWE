import os
import sys
import unittest
import json
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure scripts directory is on sys.path
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "004-work-opportunities", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from scan_opportunities import CandidateProfile
import sync_opportunities
from sync_opportunities import (
    slugify,
    estimate_success_ratio,
    enrich_candidate,
    sync_database,
    generate_monthly_audit,
)


class TestSyncOpportunities(unittest.TestCase):
    def setUp(self):
        self.profile = CandidateProfile(
            name="Diego Perea",
            location="Querétaro, Mexico",
            work_authorization="None",
            disallowed_industries=["crypto", "web3"],
            target_hours="20-30"
        )

    def test_slugify(self):
        # Basic slug generation with 2-digit zero padding
        slug1 = slugify("Zest AI", "Data Scientist", 1)
        self.assertEqual(slug1, "opp-01-zest-ai-data-scientist")

        slug9 = slugify("Acme Corp", "SWE Intern", 9)
        self.assertEqual(slug9, "opp-09-acme-corp-swe-intern")

        # 3-digit IDs
        slug100 = slugify("Stripe", "PhD Data Scientist Intern", 100)
        self.assertEqual(slug100, "opp-100-stripe-phd-data-scientist-intern")

        # Special characters stripping and hyphens collapse
        slug_special = slugify("A&B Corp.", "C++ / AI Engineer!", 5)
        self.assertEqual(slug_special, "opp-05-a-b-corp-c-ai-engineer")

    def test_estimate_success_ratio_tiers(self):
        # Tier 1: 85% - 95%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 1", self.profile, "Data Scientist", "Mexico City")
        self.assertEqual(ratio, "85% - 95%")
        self.assertAlmostEqual(min_val, 0.85)
        self.assertAlmostEqual(max_val, 0.95)
        self.assertTrue(len(just) > 10)

        # Tier 2 Intern: 65% - 80%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 2", self.profile, "Data Science Intern", "Remote")
        self.assertEqual(ratio, "65% - 80%")
        self.assertAlmostEqual(min_val, 0.65)
        self.assertAlmostEqual(max_val, 0.80)

        # Tier 2 New Grad / Full-Time: 45% - 60%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 2", self.profile, "New Grad Data Scientist", "Remote")
        self.assertEqual(ratio, "45% - 60%")
        self.assertAlmostEqual(min_val, 0.45)
        self.assertAlmostEqual(max_val, 0.60)

        # Tier 3 Standard Elite Sponsor: 25% - 45%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 3", self.profile, "Data Scientist Intern", "Mountain View, CA")
        self.assertEqual(ratio, "25% - 45%")
        self.assertAlmostEqual(min_val, 0.25)
        self.assertAlmostEqual(max_val, 0.45)

        # Tier 3 Quant: 20% - 40%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 3", self.profile, "Quantitative Research Intern", "New York, NY")
        self.assertEqual(ratio, "20% - 40%")
        self.assertAlmostEqual(min_val, 0.20)
        self.assertAlmostEqual(max_val, 0.40)

        # Tier 4 Canadian / International: 35% - 50%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 4", self.profile, "AI Co-op", "Toronto, ON, Canada")
        self.assertEqual(ratio, "35% - 50%")
        self.assertAlmostEqual(min_val, 0.35)
        self.assertAlmostEqual(max_val, 0.50)

        # Tier 5 General Domestic: 15% - 30%
        ratio, min_val, max_val, just = estimate_success_ratio("Tier 5", self.profile, "Data Analyst", "Austin, TX")
        self.assertEqual(ratio, "15% - 30%")
        self.assertAlmostEqual(min_val, 0.15)
        self.assertAlmostEqual(max_val, 0.30)

    def test_enrich_candidate_schema(self):
        raw_opp = {
            "source_id": "jobright-data-analysis-new-grad",
            "source_name": "Jobright 2026 Data Analysis New Grad",
            "company": "Zest AI",
            "role": "Data Scientist",
            "location": "Burbank, CA, United States (Remote)",
            "salary": "$90,000 - $135,000 / yr",
            "apply_url": "https://jobright.ai/jobs/info/6ac40d87372c01f6cd733b91",
            "position_type": "Full-Time",
            "hours_per_week": "Full-Time (40 hrs/week)",
            "tier_category": "Tier 2: Remote & Flexible Opportunities"
        }

        enriched = enrich_candidate(raw_opp, self.profile, 1)

        expected_keys = [
            "id", "numeric_id", "company", "role", "tier", "location",
            "work_arrangement", "hours_per_week", "compensation",
            "realistic_success_ratio", "success_ratio_min", "success_ratio_max",
            "success_ratio_justification", "urgency", "strategic_action",
            "source_repo", "apply_url", "vault_note", "status",
            "application_status", "key_points_to_highlight",
            "key_considerations", "missing_or_bridge_skills"
        ]

        for k in expected_keys:
            self.assertIn(k, enriched, f"Missing key in enriched schema: {k}")

        self.assertEqual(enriched["id"], "opp-01-zest-ai-data-scientist")
        self.assertEqual(enriched["numeric_id"], 1)
        self.assertEqual(enriched["company"], "Zest AI")
        self.assertEqual(enriched["role"], "Data Scientist")
        self.assertEqual(enriched["status"], "eligible")
        self.assertEqual(enriched["application_status"], "wishlist")
        self.assertIsInstance(enriched["key_points_to_highlight"], list)
        self.assertIsInstance(enriched["key_considerations"], list)
        self.assertIsInstance(enriched["missing_or_bridge_skills"], list)
        self.assertTrue(len(enriched["key_points_to_highlight"]) > 0)
        self.assertTrue(len(enriched["key_considerations"]) > 0)
        self.assertTrue(len(enriched["missing_or_bridge_skills"]) > 0)

    def test_sync_database_merging_and_deduplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "opportunities.json")
            csv_path = os.path.join(tmpdir, "opportunities.csv")

            existing_db = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "Career Vault Opportunities Database",
                "total_records": 1,
                "opportunities": [
                    {
                        "id": "opp-01-google-data-scientist",
                        "numeric_id": 1,
                        "company": "Google",
                        "role": "Data Scientist",
                        "tier": "Tier 3: Elite Target Hubs (Visa Sponsorship Track)",
                        "location": "Mountain View, CA",
                        "work_arrangement": "Internship / Co-op",
                        "hours_per_week": "20-30 hrs/week",
                        "compensation": "$55 / hr",
                        "realistic_success_ratio": "25% - 45%",
                        "urgency": "Standard",
                        "strategic_action": "Target Early Application",
                        "apply_url": "https://careers.google.com/jobs/101",
                        "vault_note": "004-work-opportunities/eligible/opp-01-google-data-scientist.md",
                        "status": "eligible",
                        "application_status": "wishlist"
                    }
                ]
            }
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(existing_db, f, indent=2)

            new_candidates = [
                # Duplicate by URL
                {
                    "company": "Google Inc",
                    "role": "DS Intern",
                    "location": "Mountain View",
                    "apply_url": "https://careers.google.com/jobs/101/"
                },
                # Duplicate by Company & Role
                {
                    "company": "Google",
                    "role": "Data Scientist",
                    "location": "Sunnyvale, CA",
                    "apply_url": "https://careers.google.com/jobs/999"
                },
                # Fresh new candidate 1
                {
                    "company": "Microsoft",
                    "role": "Data Science Intern",
                    "location": "Redmond, WA",
                    "apply_url": "https://apply.careers.microsoft.com/jobs/201"
                },
                # Fresh new candidate 2
                {
                    "company": "Figma",
                    "role": "Data Scientist Intern",
                    "location": "San Francisco, CA",
                    "apply_url": "https://boards.greenhouse.io/figma/jobs/301"
                },
                # Duplicate within new_candidates batch
                {
                    "company": "Microsoft",
                    "role": "Data Science Intern",
                    "location": "Redmond, WA",
                    "apply_url": "https://apply.careers.microsoft.com/jobs/201"
                }
            ]

            added_count = sync_database(new_candidates, db_path, csv_path, self.profile, verify_links=False)
            self.assertEqual(added_count, 2)

            # Check JSON file
            with open(db_path, "r", encoding="utf-8") as f:
                updated_db = json.load(f)

            self.assertEqual(len(updated_db["opportunities"]), 3)
            self.assertEqual(updated_db["total_records"], 3)

            # Check sequential numeric IDs
            ids = [o["numeric_id"] for o in updated_db["opportunities"]]
            self.assertEqual(ids, [1, 2, 3])

            opp_msft = updated_db["opportunities"][1]
            self.assertEqual(opp_msft["numeric_id"], 2)
            self.assertEqual(opp_msft["company"], "Microsoft")
            self.assertEqual(opp_msft["id"], "opp-02-microsoft-data-science-intern")

            opp_figma = updated_db["opportunities"][2]
            self.assertEqual(opp_figma["numeric_id"], 3)
            self.assertEqual(opp_figma["company"], "Figma")
            self.assertEqual(opp_figma["id"], "opp-03-figma-data-scientist-intern")

            # Check CSV file written
            self.assertTrue(os.path.exists(csv_path))
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertEqual(len(rows), 3)
                self.assertEqual(rows[1]["Company"], "Microsoft")
                self.assertEqual(rows[2]["Company"], "Figma")

    def test_sync_database_with_link_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "opportunities.json")
            csv_path = os.path.join(tmpdir, "opportunities.csv")

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump({"total_records": 0, "opportunities": []}, f)

            cands = [
                {
                    "company": "Live Corp",
                    "role": "Data Scientist",
                    "location": "Remote",
                    "apply_url": "https://example.com/live"
                },
                {
                    "company": "Dead Corp",
                    "role": "Data Scientist",
                    "location": "Remote",
                    "apply_url": "https://example.com/dead"
                }
            ]

            def fake_check(opp):
                if "live" in opp.get("apply_url", ""):
                    return opp, True, "Active (200 OK)"
                return opp, False, "Dead Link (404)"

            with patch("sync_opportunities.check_single_link", side_effect=fake_check):
                added_count = sync_database(cands, db_path, csv_path, self.profile, verify_links=True)
                self.assertEqual(added_count, 1)

            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data["opportunities"]), 1)
            self.assertEqual(data["opportunities"][0]["company"], "Live Corp")

    def test_generate_monthly_audit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_md_path = os.path.join(tmpdir, "opportunities-audit-2026-10.md")

            opportunities = [
                {
                    "id": "opp-01-acme-mexico",
                    "numeric_id": 1,
                    "company": "Acme Mexico",
                    "role": "Data Scientist Intern",
                    "tier": "Tier 1: Mexico & Domestic Market (Direct Legal Match)",
                    "location": "Querétaro, Mexico",
                    "work_arrangement": "Internship / Co-op",
                    "hours_per_week": "20-30 hrs/week",
                    "compensation": "$25,000 MXN / mo",
                    "realistic_success_ratio": "85% - 95%",
                    "urgency": "Standard",
                    "apply_url": "https://acme.mx/jobs/1",
                    "status": "eligible",
                    "application_status": "wishlist"
                },
                {
                    "id": "opp-02-remote-ai",
                    "numeric_id": 2,
                    "company": "Remote AI",
                    "role": "Data Scientist",
                    "tier": "Tier 2: Remote & Flexible Opportunities",
                    "location": "Remote (USA / Global)",
                    "work_arrangement": "Full-Time / New Grad",
                    "hours_per_week": "Full-Time (40 hrs/week)",
                    "compensation": "$100,000 / yr",
                    "realistic_success_ratio": "45% - 60%",
                    "urgency": "⚠️ URGENT",
                    "apply_url": "https://remoteai.com/jobs/2",
                    "status": "eligible",
                    "application_status": "wishlist"
                },
                {
                    "id": "opp-03-google-ds",
                    "numeric_id": 3,
                    "company": "Google",
                    "role": "Data Scientist Intern",
                    "tier": "Tier 3: Elite Target Hubs (Visa Sponsorship Track)",
                    "location": "Mountain View, CA",
                    "work_arrangement": "Internship / Co-op",
                    "hours_per_week": "20-30 hrs/week",
                    "compensation": "$55 / hr",
                    "realistic_success_ratio": "25% - 45%",
                    "urgency": "Standard",
                    "apply_url": "https://careers.google.com/jobs/3",
                    "status": "eligible",
                    "application_status": "wishlist"
                },
                {
                    "id": "opp-04-capital-one",
                    "numeric_id": 4,
                    "company": "Capital One",
                    "role": "AI Co-op",
                    "tier": "Tier 4: Canadian Co-op & International Hubs",
                    "location": "Toronto, ON, Canada",
                    "work_arrangement": "Internship / Co-op",
                    "hours_per_week": "20-30 hrs/week",
                    "compensation": "$45 CAD / hr",
                    "realistic_success_ratio": "35% - 50%",
                    "urgency": "Standard",
                    "apply_url": "https://capitalone.ca/jobs/4",
                    "status": "eligible",
                    "application_status": "wishlist"
                },
                {
                    "id": "opp-05-local-bank",
                    "numeric_id": 5,
                    "company": "Local Bank",
                    "role": "Data Analyst",
                    "tier": "Tier 5: General Domestic (Unverified Sponsorship)",
                    "location": "Austin, TX",
                    "work_arrangement": "Full-Time",
                    "hours_per_week": "40 hrs/week",
                    "compensation": "$70,000 / yr",
                    "realistic_success_ratio": "15% - 30%",
                    "urgency": "Standard",
                    "apply_url": "https://localbank.com/jobs/5",
                    "status": "eligible",
                    "application_status": "wishlist"
                }
            ]

            content = generate_monthly_audit(opportunities, audit_md_path, self.profile, month_str="2026-10")
            self.assertTrue(os.path.exists(audit_md_path))

            # Verify frontmatter invariants
            self.assertTrue(content.startswith("---"))
            self.assertIn("cycle: cycle-2026-10", content)
            self.assertIn("candidate_profile_ref: \"001-background/preferences.md\"", content)
            self.assertIn("total_opportunities: 5", content)
            self.assertIn("tier_1_count: 1", content)
            self.assertIn("tier_2_remote_count: 1", content)
            self.assertIn("tier_3_elite_sponsors_count: 1", content)
            self.assertIn("tier_4_canada_intl_count: 1", content)
            self.assertIn("tier_5_general_us_count: 1", content)

            # Tag validation: NO pure numbers
            self.assertIn("- summer-2027", content)
            self.assertNotIn("- 2027\n", content)

            # Executive summary & breakdown
            self.assertIn("## 1. Executive Summary & Audit Scope", content)
            self.assertIn("## 2. Stratified Priority Breakdown", content)
            self.assertIn("Tier 1:", content)
            self.assertIn("Tier 2: Remote & Flexible Opportunities", content)
            self.assertIn("Tier 3: Elite Target Hubs", content)
            self.assertIn("Tier 4: Canadian Co-op", content)
            self.assertIn("Tier 5: General Domestic", content)

            # Matrix table with direct links
            self.assertIn("## 3. High-Priority Curated Matrix", content)
            self.assertIn("| # | Company | Role |", content)
            self.assertIn("[Acme Mexico Portal](https://acme.mx/jobs/1)", content)
            self.assertIn("[Google Portal](https://careers.google.com/jobs/3)", content)

    def test_enrich_candidate_swe_defaults(self):
        cand = {
            "company": "Amazon",
            "role": "Software Development Engineer Intern",
            "location": "Seattle, WA",
            "apply_url": "https://amazon.jobs/123"
        }
        enriched = enrich_candidate(cand, self.profile, 10)
        self.assertEqual(enriched["id"], "opp-10-amazon-software-development-engineer-intern")
        self.assertEqual(enriched["work_arrangement"], "Internship / Co-op")
        self.assertIn("Python/C++/Java", enriched["key_points_to_highlight"][0])
        self.assertIn("Distributed Systems", enriched["missing_or_bridge_skills"][0])

    def test_sync_database_archive_deduplication(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "opportunities.json")
            csv_path = os.path.join(tmpdir, "opportunities.csv")
            arch_path = os.path.join(tmpdir, "archived_opportunities.json")

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump({"total_records": 0, "opportunities": []}, f)

            with open(arch_path, "w", encoding="utf-8") as f:
                json.dump({
                    "opportunities": [
                        {
                            "company": "Old Corp",
                            "role": "Data Scientist",
                            "apply_url": "https://oldcorp.com/apply"
                        }
                    ]
                }, f)

            cands = [
                {
                    "company": "Old Corp",
                    "role": "Data Scientist",
                    "apply_url": "https://oldcorp.com/apply"
                },
                {
                    "company": "Brand New Corp",
                    "role": "Data Scientist",
                    "apply_url": "https://brandnew.com/apply"
                }
            ]

            added = sync_database(cands, db_path, csv_path, self.profile, verify_links=False)
            self.assertEqual(added, 1)

            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data["opportunities"]), 1)
            self.assertEqual(data["opportunities"][0]["company"], "Brand New Corp")

    def test_generate_monthly_audit_from_file_path_and_dict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "opportunities.json")
            out_path1 = os.path.join(tmpdir, "audit1.md")
            out_path2 = os.path.join(tmpdir, "audit2.md")

            data = {
                "opportunities": [
                    {
                        "company": "Figma",
                        "role": "Data Scientist",
                        "tier": "Tier 3: Elite Target Hubs",
                        "location": "San Francisco, CA",
                        "apply_url": "https://figma.com/apply",
                        "realistic_success_ratio": "25% - 45%",
                        "urgency": "Standard"
                    }
                ]
            }

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Test passing file path
            content1 = generate_monthly_audit(db_path, out_path1, self.profile, month_str="2026-11")
            self.assertTrue(os.path.exists(out_path1))
            self.assertIn("cycle: cycle-2026-11", content1)

            # Test passing dict
            content2 = generate_monthly_audit(data, out_path2, self.profile, month_str="2026-11")
            self.assertTrue(os.path.exists(out_path2))
            self.assertIn("Figma", content2)

    def test_main_cli(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pending_path = os.path.join(tmpdir, "pending.json")
            db_path = os.path.join(tmpdir, "db.json")
            csv_path = os.path.join(tmpdir, "db.csv")
            audit_path = os.path.join(tmpdir, "audit.md")

            with open(pending_path, "w", encoding="utf-8") as f:
                json.dump([
                    {
                        "company": "Apple",
                        "role": "Data Scientist",
                        "location": "Cupertino, CA",
                        "apply_url": "https://apple.com/jobs/1"
                    }
                ], f)

            test_args = [
                "sync_opportunities.py",
                "--pending", pending_path,
                "--db", db_path,
                "--csv", csv_path,
                "--audit", audit_path
            ]
            with patch.object(sys, "argv", test_args):
                sync_opportunities.main()

            self.assertTrue(os.path.exists(db_path))
            self.assertTrue(os.path.exists(csv_path))
            self.assertTrue(os.path.exists(audit_path))

    def test_sync_database_defensive_numeric_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "opportunities.json")
            csv_path = os.path.join(tmpdir, "opportunities.csv")

            existing_db = {
                "total_records": 2,
                "opportunities": [
                    {
                        "id": "opp-01-a",
                        "numeric_id": None,
                        "company": "Company A",
                        "role": "Role A",
                        "apply_url": "https://a.com"
                    },
                    {
                        "id": "opp-02-b",
                        "numeric_id": "5",
                        "company": "Company B",
                        "role": "Role B",
                        "apply_url": "https://b.com"
                    }
                ]
            }
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(existing_db, f)

            new_cands = [
                {
                    "company": "Company C",
                    "role": "Role C",
                    "apply_url": "https://c.com"
                }
            ]

            added = sync_database(new_cands, db_path, csv_path, self.profile, verify_links=False)
            self.assertEqual(added, 1)

            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            opp_c = data["opportunities"][-1]
            self.assertEqual(opp_c["numeric_id"], 6)
            self.assertEqual(opp_c["id"], "opp-06-company-c-role-c")

    def test_generate_monthly_audit_matrix_tier_priority_and_pipe_sanitization(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = os.path.join(tmpdir, "audit.md")

            # Create 30 opportunities:
            # 28 Tier 5 items followed by 2 Tier 1 items with pipes in names
            opps = []
            for i in range(1, 29):
                opps.append({
                    "id": f"opp-{i}",
                    "numeric_id": i,
                    "company": f"T5 Corp {i}",
                    "role": f"T5 Role {i}",
                    "tier": "Tier 5: General Domestic",
                    "location": "US",
                    "apply_url": f"https://example.com/t5/{i}"
                })

            opps.append({
                "id": "opp-29",
                "numeric_id": 29,
                "company": "Priority | Tech MX",
                "role": "AI | Data Intern",
                "tier": "Tier 1: Mexico & Domestic Market",
                "location": "Querétaro, Mexico",
                "apply_url": "https://example.com/t1"
            })

            content = generate_monthly_audit(opps, audit_path, self.profile, month_str="2026-10")

            # 1. Tier 1 item must appear in top matrix (first row) despite being appended late
            self.assertIn("**Priority - Tech MX**", content)
            self.assertIn("AI - Data Intern", content)
            # Pipes in company/role should be sanitized to '-'
            self.assertNotIn("Priority | Tech MX", content)
            self.assertNotIn("AI | Data Intern", content)

            # Check that first row of table is Tier 1
            matrix_start = content.find("## 3. High-Priority Curated Matrix")
            matrix_section = content[matrix_start:content.find("## 4. Deep-Dive")]
            first_row_idx = matrix_section.find("| 1 |")
            self.assertTrue(first_row_idx != -1)
            first_row = matrix_section[first_row_idx:matrix_section.find("\n", first_row_idx)]
            self.assertIn("Priority - Tech MX", first_row)
            self.assertIn("Tier 1", first_row)


if __name__ == "__main__":
    unittest.main()

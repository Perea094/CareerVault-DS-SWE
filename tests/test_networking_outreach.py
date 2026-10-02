import os
import unittest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "networking-outreach", "scripts")))
import generate_outreach

class TestNetworkingOutreach(unittest.TestCase):
    def test_generate_three_tiers(self):
        role_info = {
            "company": "Databricks",
            "role": "Data Systems Intern",
            "key_skill": "Lakehouse & Spark Optimization"
        }
        candidate_info = {
            "name": "Diego Perea León",
            "school": "Tecnológico de Monterrey",
            "highlight": "Achieved 3,700 FPS distributed RL training pipeline"
        }
        
        outreach = generate_outreach.build_outreach_templates(role_info, candidate_info)
        
        self.assertIn("alumni", outreach)
        self.assertIn("recruiter", outreach)
        self.assertIn("hiring_manager", outreach)
        
        self.assertIn("Tecnológico de Monterrey", outreach["alumni"])
        self.assertIn("Databricks", outreach["recruiter"])
        self.assertIn("3,700 FPS", outreach["hiring_manager"])

    def test_generate_outreach_markdown(self):
        role_info = {
            "company": "Tesla",
            "role": "Autopilot Software Intern",
            "key_skill": "C++ & Real-time Edge AI"
        }
        candidate_info = {
            "name": "Diego Perea León",
            "school": "Tecnológico de Monterrey",
            "highlight": "Engineered Hailo-8 NPU pipeline at 30 FPS"
        }
        md = generate_outreach.format_outreach_markdown(role_info, candidate_info)
        self.assertIn("# Networking Outreach: Tesla - Autopilot Software Intern", md)
        self.assertIn("### Tier 1: Alumni Outreach", md)
        self.assertIn("### Tier 2: Recruiter Outreach", md)
        self.assertIn("### Tier 3: Hiring Manager Outreach", md)
        self.assertIn("Hailo-8 NPU pipeline at 30 FPS", md)

    def test_custom_recipient_names(self):
        role_info = {
            "company": "Google",
            "role": "Software Engineer Intern",
            "key_skill": "Distributed Systems"
        }
        candidate_info = {
            "name": "Diego Perea León",
            "school": "Tecnológico de Monterrey",
            "highlight": "Developed high-throughput queue"
        }
        outreach = generate_outreach.build_outreach_templates(
            role_info, candidate_info, alumni_name="Alex", recruiter_name="Sarah", hm_name="Dr. Smith"
        )
        self.assertIn("Hi Alex", outreach["alumni"])
        self.assertIn("Hi Sarah", outreach["recruiter"])
        self.assertIn("Dear Dr. Smith", outreach["hiring_manager"])

if __name__ == "__main__":
    unittest.main()

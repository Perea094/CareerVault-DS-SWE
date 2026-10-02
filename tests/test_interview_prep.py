import os
import unittest
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "interview-prep", "scripts")))
import generate_dossier

class TestInterviewPrep(unittest.TestCase):
    def test_format_star_story(self):
        story = generate_dossier.format_star_story(
            title="DAVE Edge AI System",
            situation="Wanted to detect safety violations on campus without cloud latency.",
            task="Architect a real-time edge processing pipeline on limited compute.",
            action="Deployed Hailo-8 NPU on Raspberry Pi 5 with MediaPipe and custom OpenCV buffers.",
            result="Achieved 30 FPS inference with <50ms latency and won 1st place Expo Ingenierías."
        )
        self.assertIn("### DAVE Edge AI System", story)
        self.assertIn("**Situation:**", story)
        self.assertIn("**Task:**", story)
        self.assertIn("**Action:**", story)
        self.assertIn("**Result:**", story)

    def test_generate_interview_dossier_content(self):
        role_info = {
            "company": "Mistral AI",
            "role": "AI Research Engineer Intern",
            "tech_stack": ["PyTorch", "vLLM", "C++", "CUDA"]
        }
        background_assets = [
            {
                "title": "Ape-X DQN Street Fighter II",
                "metrics": "3,700 FPS on distributed actors",
                "star": {
                    "s": "Need high throughput RL.",
                    "t": "Scale distributed experience replay.",
                    "a": "Implemented custom vectorized environments.",
                    "r": "Reached 3,700 FPS and 85% win rate."
                }
            }
        ]
        markdown = generate_dossier.build_dossier_markdown(role_info, background_assets)
        self.assertIn("# Interview Preparation Dossier: Mistral AI", markdown)
        self.assertIn("Ape-X DQN Street Fighter II", markdown)
        self.assertIn("## 3. Technical Question Bank & Architectural Drills", markdown)
        self.assertIn("## 2. Behavioral STAR Grid (Grounded in Verified Background)", markdown)

if __name__ == "__main__":
    unittest.main()

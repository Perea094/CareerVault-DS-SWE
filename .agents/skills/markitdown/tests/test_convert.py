import subprocess
import sys
import json
from pathlib import Path

def test_convert_text_file(tmp_path):
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("# Linear Programming\n\nIntroduction to simplex.", encoding="utf-8")
    
    script = Path(__file__).resolve().parents[1] / "scripts" / "convert.py"
    cmd = [sys.executable, str(script), "--input", str(sample_file), "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    data = json.loads(proc.stdout)
    assert "text" in data
    assert "Linear Programming" in data["text"]
    assert data["ext"] == ".txt"
    assert data["title"] == "Linear Programming"

def test_convert_missing_file():
    script = Path(__file__).resolve().parents[1] / "scripts" / "convert.py"
    cmd = [sys.executable, str(script), "--input", "non_existent_file.pdf", "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode != 0
    assert "Error" in proc.stderr or "not found" in proc.stderr

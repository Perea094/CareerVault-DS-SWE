import pytest
from pathlib import Path
import sys

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from vault_helper import scan_vault_structure, match_courses_and_topics

def test_scan_vault_structure(tmp_path):
    # Setup mock semesters
    sem5 = tmp_path / "005-Quinto Semestre"
    course_opt = sem5 / "003-Optimización estocástica"
    course_opt.mkdir(parents=True)
    (course_opt / "002-Relación con el método simplex.md").write_text("Simplex y teoría de juegos", encoding="utf-8")
    
    sem6 = tmp_path / "006-Sexto Semestre"
    course_ml = sem6 / "001-Machine Learning Avanzado"
    course_ml.mkdir(parents=True)
    
    structure = scan_vault_structure(tmp_path)
    
    assert "005-Quinto Semestre" in structure
    assert "003-Optimización estocástica" in structure["005-Quinto Semestre"]
    assert "006-Sexto Semestre" in structure
    assert "001-Machine Learning Avanzado" in structure["006-Sexto Semestre"]

def test_match_courses_and_topics(tmp_path):
    sem = tmp_path / "005-Quinto Semestre"
    c1 = sem / "003-Optimización estocástica"
    c2 = sem / "006-Criptografía"
    c1.mkdir(parents=True)
    c2.mkdir(parents=True)
    
    sample_text = "En esta clase resolvemos problemas usando optimización estocástica y programación lineal."
    matches = match_courses_and_topics(sample_text, vault_root=tmp_path)
    
    assert len(matches) > 0
    assert matches[0]["course_name"] == "003-Optimización estocástica"

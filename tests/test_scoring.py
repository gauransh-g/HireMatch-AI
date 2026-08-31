from app.services.jd_analyzer import analyze_jd
from app.services.scoring_engine import calculate_score

def test_scoring_prefers_skill_match():
    jd_desc = (
        "We need a backend engineer with Python, FastAPI, Docker, PostgreSQL, "
        "and AWS experience. Experience required: 5 years."
    )
    job_profile = analyze_jd("Backend Engineer", jd_desc)
    
    cand_a = {
        "name": "Candidate A",
        "experience_years": 5.0,
        "skills": ["python", "fastapi", "postgresql", "docker", "aws"],
        "education": ["B.S. Computer Science"],
        "projects": ["Built REST APIs in Python"],
        "resume_text": "Candidate A. 5 years experience. Python, FastAPI, PostgreSQL, Docker, AWS. Created backend projects."
    }
    
    cand_b = {
        "name": "Candidate B",
        "experience_years": 6.0,
        "skills": ["java", "spring", "mysql"],
        "education": ["B.S. Computer Science"],
        "projects": ["Built Java applications"],
        "resume_text": "Candidate B. 6 years experience. Java developer working on Spring Boot and MySQL."
    }
    
    score_a = calculate_score(cand_a, job_profile)
    score_b = calculate_score(cand_b, job_profile)
    
    assert score_a["overall_score"] > score_b["overall_score"]
    assert "python" in score_a["matched_skills"]
    assert "fastapi" in score_a["matched_skills"]
    assert len(score_b["missing_skills"]) > 0

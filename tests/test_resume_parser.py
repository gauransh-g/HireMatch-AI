from app.services.resume_parser import extract_candidate_profile

def test_extract_candidate_profile_from_name_and_experience_lines():
    text = "Name: Prashant Singh Email: prashant@gmail.com Years of Experience: 3"
    profile = extract_candidate_profile(text, "resume.pdf")

    assert profile["name"] == "Prashant Singh"
    assert profile["experience_years"] == 3.0
    assert "education" in profile
    assert "projects" in profile

def test_extract_candidate_profile_from_email_and_fallback():
    text = "Contact: ananya.verma98@example.com Built backend APIs with Python."
    profile = extract_candidate_profile(text, "candidate_profile.docx")

    assert profile["name"] == "Ananya Verma"
    assert profile["experience_years"] == 0.0

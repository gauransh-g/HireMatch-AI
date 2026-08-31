from app.services.skill_extractor import extract_skills
from app.services.semantic_matcher import get_semantic_skill_matches, get_text_similarity

def calculate_score(candidate_profile: dict, job_profile: dict) -> dict:
    """
    Multi-component weighted match score.
    Weights: Skill(35%) | Experience(25%) | Responsibility(20%) | Education(10%) | Semantic(10%)
    """
    resume_text = candidate_profile["resume_text"]
    resume_skills = set(candidate_profile["skills"])

    jd_desc = job_profile["description"]
    req_skills = job_profile["required_skills"]
    pref_skills = job_profile["preferred_skills"]
    req_exp = job_profile["experience_required"]

    # 1. Skill Match (35%)
    exact_req = resume_skills.intersection(req_skills)
    sem_req_map = get_semantic_skill_matches(req_skills, resume_skills)
    sem_req = set(sem_req_map.keys())

    req_len = len(req_skills)
    req_score = 1.0 if req_len == 0 else min(1.0, (len(exact_req) + 0.6 * len(sem_req)) / req_len)

    exact_pref = resume_skills.intersection(pref_skills)
    sem_pref_map = get_semantic_skill_matches(pref_skills, resume_skills)
    sem_pref = set(sem_pref_map.keys())

    pref_len = len(pref_skills)
    pref_score = 1.0 if pref_len == 0 else min(1.0, (len(exact_pref) + 0.6 * len(sem_pref)) / pref_len)

    skill_score = (0.75 * req_score + 0.25 * pref_score) * 100.0

    matched_skills = sorted(list(exact_req.union(sem_req).union(exact_pref).union(sem_pref)))
    missing_required = [s for s in req_skills if s not in exact_req and s not in sem_req]
    missing_preferred = [s for s in pref_skills if s not in exact_pref and s not in sem_pref]
    missing_skills = sorted(missing_required + missing_preferred)

    # 2. Experience Match (25%)
    cand_exp = candidate_profile["experience_years"]
    if req_exp == 0:
        experience_score = 100.0
    elif cand_exp >= req_exp:
        experience_score = 100.0
    else:
        experience_score = (cand_exp / req_exp) * 100.0

    # 3. Responsibility Match (20%)
    raw_sim = get_text_similarity(resume_text, jd_desc)
    responsibility_score = max(20.0, min(100.0, raw_sim * 220.0))

    # 4. Education Match (10%)
    edu_list = candidate_profile["education"]
    jd_lower = jd_desc.lower()
    has_degree_req = any(x in jd_lower for x in ["degree", "bachelor", "master", "phd", "education", "bs ", "ms "])

    if not has_degree_req:
        education_score = 100.0
    else:
        edu_text = " ".join(edu_list).lower()
        if any(x in edu_text for x in ["ph.d", "phd", "doctorate"]):
            education_score = 100.0
        elif any(x in edu_text for x in ["master", "m.s", "ms", "mtech"]):
            education_score = 95.0
        elif any(x in edu_text for x in ["bachelor", "b.s", "bs", "btech"]):
            education_score = 85.0
        elif any(x in edu_text for x in ["diploma", "associate"]):
            education_score = 65.0
        elif len(edu_list) > 0:
            education_score = 55.0
        else:
            education_score = 30.0

    # 5. Semantic Similarity (10%)
    candidate_profile_text = f"{' '.join(candidate_profile['skills'])} {' '.join(candidate_profile['projects'])}"
    raw_sem_sim = get_text_similarity(candidate_profile_text, jd_desc)
    semantic_score = max(25.0, min(100.0, raw_sem_sim * 240.0))

    # Overall Score
    overall_score = round(min(100.0, max(0.0,
        (0.35 * skill_score) +
        (0.25 * experience_score) +
        (0.20 * responsibility_score) +
        (0.10 * education_score) +
        (0.10 * semantic_score)
    )), 1)

    skill_score = round(skill_score, 1)
    experience_score = round(experience_score, 1)
    responsibility_score = round(responsibility_score, 1)
    education_score = round(education_score, 1)
    semantic_score = round(semantic_score, 1)

    # Explainability
    strengths = []
    concerns = []

    if req_exp > 0:
        if cand_exp >= req_exp:
            strengths.append(f"Exceeds experience requirement ({cand_exp:.1f} yrs vs {req_exp:.1f} yrs required)")
        elif cand_exp >= req_exp * 0.7:
            strengths.append(f"Near experience target ({cand_exp:.1f} yrs vs {req_exp:.1f} yrs required)")
        else:
            concerns.append(f"Below required experience ({cand_exp:.1f} yrs vs {req_exp:.1f} yrs required)")
    elif cand_exp > 0:
        strengths.append(f"Has {cand_exp:.1f} years of relevant experience")

    matching_req = exact_req.union(sem_req)
    if matching_req:
        strengths.append(f"Matches {len(matching_req)} required skills: {', '.join(sorted(list(matching_req)))}")
    if missing_required:
        concerns.append(f"Missing required skills: {', '.join(missing_required)}")

    if sem_req or sem_pref:
        sem_list = sorted(list(sem_req.union(sem_pref)))
        strengths.append(f"Demonstrates adjacent competence for: {', '.join(sem_list)}")

    if education_score >= 85.0:
        strengths.append("Suitable educational background detected")
    elif has_degree_req and education_score < 60.0:
        concerns.append("No clear degree matching JD requirements")

    if responsibility_score >= 80.0:
        strengths.append("Strong alignment with job responsibilities")
    elif responsibility_score < 40.0:
        concerns.append("Low overlap with described role responsibilities")

    if overall_score >= 85.0:
        rating, rec = "Strong Match", "Excellent candidate who meets almost all requirements."
    elif overall_score >= 70.0:
        rating, rec = "Moderate Match", "Good candidate covering core requirements with some gaps."
    else:
        rating, rec = "Weak Match", "Candidate has significant gaps in required skills or experience."

    gap_text = f" Gaps: {', '.join(missing_required)}." if missing_required else ""
    summary = f"{rating}. {rec}{gap_text} Overall match: {overall_score:.0f}%."

    return {
        "overall_score": overall_score,
        "skill_score": skill_score,
        "experience_score": experience_score,
        "responsibility_score": responsibility_score,
        "education_score": education_score,
        "semantic_score": semantic_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": strengths,
        "concerns": concerns,
        "summary": summary
    }

import re
from app.services.skill_extractor import extract_skills, normalize_text
from app.schemas.schemas import RoleFamily

ROLE_KEYWORDS = {
    "backend": ["backend", "api", "microservice", "server-side", "django", "fastapi", "spring boot", "node"],
    "frontend": ["frontend", "ui", "ux", "web", "react", "angular", "vue", "typescript", "css"],
    "data_ai": ["data", "ml", "ai", "machine learning", "nlp", "llm", "deep learning", "pytorch", "tensorflow", "python"],
    "devops": ["devops", "sre", "platform", "infra", "kubernetes", "docker", "terraform", "ci/cd", "jenkins", "aws", "gcp"],
    "fullstack": ["full stack", "fullstack", "frontend and backend"],
}

def infer_role_family(job_title: str, job_description: str) -> RoleFamily:
    """Infer the role family based on job title and description text keywords."""
    text = normalize_text(f"{job_title} {job_description}")
    scores = {role: 0 for role in ROLE_KEYWORDS}
    for role, keywords in ROLE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[role] += 1
                
    inferred = max(scores, key=lambda role: scores[role])
    if scores[inferred] == 0:
        return "backend"
    return inferred

def analyze_jd(job_title: str, job_description: str) -> dict:
    """Parse a job description into structured sections, identifying required/preferred skills and experience."""
    role = infer_role_family(job_title, job_description)
    
    # Extract years of experience (e.g., 3+ years, 5 years)
    # Ignore values > 15 to filter out year numbers like 2024/2026.
    exp_matches = re.findall(r"\b(\d+)\+?\s*(?:years?|yrs?|years?\s+of\s+experience)\b", job_description.lower())
    experience = 0.0
    if exp_matches:
        valid_exps = [float(x) for x in exp_matches if float(x) <= 15]
        if valid_exps:
            experience = max(valid_exps)
            
    # Section matching
    lines = job_description.split("\n")
    required_text = []
    preferred_text = []
    current_section = "general"
    
    req_headers = ["required", "requirements", "must-have", "must have", "key qualifications", "what you need", "what we look for"]
    pref_headers = ["preferred", "nice-to-have", "nice to have", "plus", "desired", "bonus", "assets", "would be a plus"]
    
    for line in lines:
        cleaned_line = line.strip().lower()
        if not cleaned_line:
            continue
        
        # Check if line contains a section header
        if any(h in cleaned_line for h in req_headers):
            current_section = "required"
            continue
        elif any(h in cleaned_line for h in pref_headers):
            current_section = "preferred"
            continue
        elif cleaned_line.endswith(":") and len(cleaned_line) < 30:
            current_section = "general"
            continue
            
        if current_section == "required":
            required_text.append(line)
        elif current_section == "preferred":
            preferred_text.append(line)
            
    all_skills = extract_skills(job_description)
    
    if required_text:
        req_skills = extract_skills(" ".join(required_text))
    else:
        req_skills = all_skills.copy()
        
    if preferred_text:
        pref_skills = extract_skills(" ".join(preferred_text))
    else:
        pref_skills = all_skills.difference(req_skills)
        
    # Clean overlap
    pref_skills = pref_skills.difference(req_skills)
    
    return {
        "role": role,
        "experience_required": experience,
        "required_skills": sorted(list(req_skills)),
        "preferred_skills": sorted(list(pref_skills)),
        "description": job_description,
        "title": job_title
    }

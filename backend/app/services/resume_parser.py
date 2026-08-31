from io import BytesIO
from pathlib import Path
import re
from docx import Document
from pypdf import PdfReader
from app.services.skill_extractor import extract_skills

class ResumeParsingError(ValueError):
    pass

def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def parse_resume_bytes(file_name: str, content: bytes) -> str:
    """Read bytes of DOCX, PDF, or TXT file and return cleaned text."""
    extension = Path(file_name).suffix.lower()

    if extension == ".pdf":
        return _parse_pdf(content)
    if extension == ".docx":
        return _parse_docx(content)
    if extension == ".txt":
        return _parse_txt(content)

    raise ResumeParsingError(
        f"Unsupported resume format '{extension}'. Use PDF, DOCX, or TXT."
    )

def _parse_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = _clean_text(" ".join(pages))
        if not text:
            raise ResumeParsingError("Could not extract text from PDF resume.")
        return text
    except Exception as e:
        raise ResumeParsingError(f"Error parsing PDF resume: {str(e)}")

def _parse_docx(content: bytes) -> str:
    try:
        document = Document(BytesIO(content))
        text = _clean_text(" ".join(paragraph.text for paragraph in document.paragraphs))
        if not text:
            raise ResumeParsingError("Could not extract text from DOCX resume.")
        return text
    except Exception as e:
        raise ResumeParsingError(f"Error parsing DOCX resume: {str(e)}")

def _parse_txt(content: bytes) -> str:
    try:
        text = _clean_text(content.decode("utf-8", errors="ignore"))
        if not text:
            raise ResumeParsingError("Could not extract text from TXT resume.")
        return text
    except Exception as e:
        raise ResumeParsingError(f"Error parsing TXT resume: {str(e)}")

def extract_candidate_profile(resume_text: str, fallback_file_name: str) -> dict:
    """Parse resume text and return structured candidate metadata."""
    name = _extract_name(resume_text, fallback_file_name)
    years_experience = _extract_years_experience(resume_text)
    skills = sorted(list(extract_skills(resume_text)))
    education = _extract_education(resume_text)
    projects = _extract_projects(resume_text)
    
    return {
        "name": name,
        "experience_years": years_experience,
        "skills": skills,
        "education": education,
        "projects": projects,
        "resume_text": resume_text
    }

def _extract_name(resume_text: str, fallback_file_name: str) -> str:
    text = _clean_text(resume_text)

    name_patterns = [
        r"\bname\b\s*[:\-]\s*([a-zA-Z][a-zA-Z\s.'-]{1,60}?)(?=\s+(?:email|phone|mobile|years?\s+of\s+experience)\b|$)",
        r"\bfull\s+name\b\s*[:\-]\s*([a-zA-Z][a-zA-Z\s.'-]{1,60}?)(?=\s+(?:email|phone|mobile|years?\s+of\s+experience)\b|$)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _titlecase_name(match.group(1))

    email_match = re.search(r"([a-zA-Z0-9_.+-]+)@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if email_match:
        local_part = email_match.group(1).replace(".", " ").replace("_", " ").replace("-", " ")
        candidate = re.sub(r"\d+", "", local_part).strip()
        if candidate:
            return _titlecase_name(candidate)

    return _fallback_name_from_file(fallback_file_name)

def _extract_years_experience(resume_text: str) -> float:
    text = _clean_text(resume_text)
    year_values: list[float] = []

    patterns = [
        r"years?\s+of\s+experience\s*[:\-]\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"experience\s*[:\-]\s*(\d+(?:\.\d+)?)\+?\s*years?",
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+experience",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for value in matches:
            year_values.append(float(value))

    if year_values:
        val = max(year_values)
        if val <= 35:
            return round(val, 1)

    return 0.0

def _extract_education(resume_text: str) -> list[str]:
    """Extract education background, scanning sentences for degrees and academic keywords."""
    # Split text into clean sentences/clauses using punctuation or spacing
    sentences = re.split(r"[.!?•|]", resume_text)
    education = []
    edu_keywords = ["university", "college", "degree", "bachelor", "master", "phd", "b.s", "m.s", "btech", "mtech", "diploma", "education", "institutions"]
    for s in sentences:
        cleaned = _clean_text(s)
        if len(cleaned) < 10 or len(cleaned) > 150:
            continue
        if any(keyword in cleaned.lower() for keyword in edu_keywords):
            education.append(cleaned)
            
    seen = set()
    result = []
    for item in education:
        if item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result[:3]

def _extract_projects(resume_text: str) -> list[str]:
    """Scan resume sentences for project work, utilizing building action verbs."""
    sentences = re.split(r"[.!?•|]", resume_text)
    projects = []
    project_keywords = ["project", "built", "developed", "implemented", "designed", "created", "git repo", "github.com/"]
    for s in sentences:
        cleaned = _clean_text(s)
        if len(cleaned) < 20 or len(cleaned) > 180:
            continue
        if any(kw in cleaned.lower() for kw in project_keywords):
            # Ignore sentences that are purely educational or job experiences
            if not any(ek in cleaned.lower() for ek in ["experience years", "university", "college", "job title", "work authorization"]):
                projects.append(cleaned)
                
    seen = set()
    result = []
    for item in projects:
        if item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result[:4]

def _titlecase_name(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split() if part)

def _fallback_name_from_file(file_name: str) -> str:
    stem = Path(file_name).stem
    normalized = re.sub(r"[_\-.]+", " ", stem).strip()
    if not normalized:
        return "Candidate"
    return _titlecase_name(normalized)

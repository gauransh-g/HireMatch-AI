from app.utils.tfidf import calculate_cosine_similarity
from app.services.skill_extractor import normalize_skill_name

RELATED_SKILL_GRAPH = {
    "python": {"django", "flask", "fastapi", "pandas", "numpy", "scikit-learn"},
    "javascript": {"typescript", "react", "node"},
    "typescript": {"javascript", "react", "node"},
    "sql": {"postgresql", "mongodb", "mysql", "redis", "elasticsearch"},
    "postgresql": {"sql", "mysql", "redis"},
    "mysql": {"sql", "postgresql", "redis"},
    "machine learning": {"pytorch", "tensorflow", "scikit-learn", "numpy", "pandas", "llm", "nlp"},
    "llm": {"nlp", "rag", "machine learning", "pytorch"},
    "nlp": {"llm", "machine learning", "pytorch"},
    "aws": {"docker", "kubernetes", "terraform", "github actions", "jenkins", "azure", "gcp"},
    "azure": {"docker", "kubernetes", "terraform", "github actions", "jenkins", "aws", "gcp"},
    "gcp": {"docker", "kubernetes", "terraform", "github actions", "jenkins", "aws", "azure"},
    "kubernetes": {"docker", "terraform", "aws", "azure", "gcp"},
    "terraform": {"kubernetes", "aws", "azure", "gcp"},
    "ci/cd": {"jenkins", "github actions", "docker"},
}

def get_semantic_skill_matches(target_skills: list[str], candidate_skills: set[str]) -> dict[str, list[str]]:
    semantic_matches: dict[str, list[str]] = {}
    for skill in target_skills:
        normalized_skill = normalize_skill_name(skill)
        if normalized_skill in candidate_skills:
            continue
        related = RELATED_SKILL_GRAPH.get(normalized_skill, set())
        supports = sorted(candidate_skills.intersection(related))
        if supports:
            semantic_matches[normalized_skill] = supports
    return semantic_matches

def get_text_similarity(doc1: str, doc2: str) -> float:
    return calculate_cosine_similarity(doc1, doc2)

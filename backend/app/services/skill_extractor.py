import re

TECH_SKILLS = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "sql", "ruby", "rust", "php", "scala", "kotlin", "swift", "objective-c"
    ],
    "frameworks": [
        "fastapi", "django", "flask", "spring", "react", "node", "dotnet", "pytorch", "tensorflow", "angular", "vue", "express", "rails", "laravel"
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "github actions", "gitlab", "ansible", "prometheus", "grafana"
    ],
    "data_ai": [
        "machine learning", "nlp", "llm", "rag", "pandas", "numpy", "scikit-learn", "postgresql", "mongodb", "redis", "mysql", "elasticsearch", "spark", "hadoop", "tableau"
    ],
}

SKILL_ALIASES = {
    "py": "python",
    "nodejs": "node",
    "node.js": "node",
    ".net": "dotnet",
    "dotnet": "dotnet",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "k8s": "kubernetes",
    "tf": "terraform",
    "js": "javascript",
    "ts": "typescript",
    "ml": "machine learning",
    "genai": "llm",
    "large language model": "llm",
    "large language models": "llm",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "django framework": "django",
    "reactjs": "react",
    "react.js": "react",
    "git": "ci/cd",
    "mysql db": "mysql",
    "spark sql": "spark"
}

CANONICAL_SKILLS = {skill for group in TECH_SKILLS.values() for skill in group}

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()

def _contains_term(text: str, term: str) -> bool:
    # Match term surrounded by word boundaries (or special tech boundary patterns)
    pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
    return re.search(pattern, text) is not None

def normalize_skill_name(skill: str) -> str:
    normalized = normalize_text(skill)
    return SKILL_ALIASES.get(normalized, normalized)

def extract_skills(text: str) -> set[str]:
    """Scan text against taxonomy and aliases to find technical skills."""
    normalized = normalize_text(text)
    found: set[str] = set()

    for skill in CANONICAL_SKILLS:
        if _contains_term(normalized, skill):
            found.add(skill)

    for alias, canonical in SKILL_ALIASES.items():
        if _contains_term(normalized, alias):
            found.add(canonical)

    return found

def normalize_skill_list(skills: list[str]) -> list[str]:
    cleaned = {
        normalize_skill_name(skill)
        for skill in skills
        if normalize_skill_name(skill)
    }
    return sorted(cleaned)

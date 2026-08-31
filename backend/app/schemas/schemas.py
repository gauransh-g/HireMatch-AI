from typing import Literal
from pydantic import BaseModel, Field

RoleFamily = Literal["backend", "frontend", "data_ai", "devops", "fullstack"]

class JobCreate(BaseModel):
    title: str = Field(..., min_length=2)
    description: str = Field(..., min_length=10)
    role_family: RoleFamily | None = None
    must_have_skills: list[str] = Field(default_factory=list)
    nice_to_have_skills: list[str] = Field(default_factory=list)

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    role_family: RoleFamily
    experience_required: float
    required_skills: list[str]
    preferred_skills: list[str]
    created_at: str

    class Config:
        from_attributes = True

class CandidateInputSchema(BaseModel):
    name: str = Field(..., min_length=1)
    resume_text: str = Field(..., min_length=10)
    years_experience: float = Field(0.0, ge=0)

class CandidateResponse(BaseModel):
    id: int
    job_id: int
    name: str
    experience_years: float
    skills: list[str]
    education: list[str]
    projects: list[str]
    created_at: str

    class Config:
        from_attributes = True

class MatchResultResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    overall_score: float
    skill_score: float
    experience_score: float
    responsibility_score: float
    education_score: float
    semantic_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    summary: str
    candidate_name: str | None = None
    experience_years: float | None = None

    class Config:
        from_attributes = True

class JobAnalysisResult(BaseModel):
    role: str
    experience: float
    required_skills: list[str]
    preferred_skills: list[str]

class ScreenRequest(BaseModel):
    job_id: int
    candidate_ids: list[int] | None = None  # None means screen all unscreened candidates

class CompareResponse(BaseModel):
    candidate_a: MatchResultResponse
    candidate_b: MatchResultResponse

class DashboardMetricsResponse(BaseModel):
    active_jobs: int
    total_candidates: int
    avg_match: float
    top_candidates: int

class UploadProfilePreview(BaseModel):
    file_name: str
    status: Literal["ok", "error"]
    candidate_name: str | None = None
    years_experience: float | None = None
    detected_skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    message: str | None = None

class PreviewFilesResponse(BaseModel):
    previews: list[UploadProfilePreview]

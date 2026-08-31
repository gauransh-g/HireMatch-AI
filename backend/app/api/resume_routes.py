from typing import Annotated
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from app.schemas.schemas import PreviewFilesResponse, UploadProfilePreview, CandidateResponse
from app.services.resume_parser import (
    ResumeParsingError,
    extract_candidate_profile,
    parse_resume_bytes,
)
from app.models import database as db

router = APIRouter(prefix="/v1/resumes", tags=["resumes"])

@router.post("/preview", response_model=PreviewFilesResponse)
async def preview_files(resumes: Annotated[list[UploadFile], File(...)]) -> PreviewFilesResponse:
    """Parse uploaded resumes and return structured profile previews (without database persistence)."""
    previews: list[UploadProfilePreview] = []

    for idx, resume in enumerate(resumes):
        file_name = resume.filename or f"candidate-{idx + 1}.txt"
        try:
            content = await resume.read()
            resume_text = parse_resume_bytes(file_name, content)
            profile = extract_candidate_profile(resume_text, file_name)

            previews.append(
                UploadProfilePreview(
                    file_name=file_name,
                    status="ok",
                    candidate_name=profile.get("name"),
                    years_experience=profile.get("experience_years"),
                    detected_skills=profile.get("skills", [])[:8],
                    education=profile.get("education", []),
                    projects=profile.get("projects", []),
                    message="Profile parsed successfully.",
                )
            )
        except ResumeParsingError as exc:
            previews.append(UploadProfilePreview(file_name=file_name, status="error", message=str(exc)))
        except Exception as e:
            previews.append(UploadProfilePreview(file_name=file_name, status="error", message=f"System error: {str(e)}"))

    return PreviewFilesResponse(previews=previews)

@router.post("/upload", response_model=list[CandidateResponse])
async def upload_resumes(
    job_id: Annotated[int, Form(...)],
    resumes: Annotated[list[UploadFile], File(...)]
):
    """Parse uploaded resumes and save them to SQLite as candidates linked to a job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    saved_candidates = []
    for idx, resume in enumerate(resumes):
        file_name = resume.filename or f"candidate-{idx + 1}.txt"
        try:
            content = await resume.read()
            resume_text = parse_resume_bytes(file_name, content)
            profile = extract_candidate_profile(resume_text, file_name)

            cand_id = db.add_candidate(
                job_id=job_id,
                name=profile["name"],
                experience_years=profile["experience_years"],
                skills=profile["skills"],
                education=profile["education"],
                projects=profile["projects"],
                resume_text=resume_text
            )

            cand_data = db.get_candidate(cand_id)
            if cand_data:
                saved_candidates.append(CandidateResponse(**cand_data))
        except ResumeParsingError as exc:
            raise HTTPException(status_code=400, detail=f"Error parsing '{file_name}': {str(exc)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error uploading '{file_name}': {str(e)}")

    return saved_candidates

@router.get("/job/{job_id}", response_model=list[CandidateResponse])
def get_candidates_for_job(job_id: int):
    """Retrieve all candidates associated with a job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    candidates = db.get_candidates_for_job(job_id)
    return [CandidateResponse(**c) for c in candidates]

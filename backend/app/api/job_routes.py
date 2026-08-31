from fastapi import APIRouter, HTTPException
from app.schemas.schemas import JobCreate, JobResponse, JobAnalysisResult
from app.services.jd_analyzer import analyze_jd
from app.models import database as db

router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse)
def create_job(request: JobCreate):
    """Analyze the job description, extract required/preferred skills & experience, and save to SQLite."""
    try:
        analysis = analyze_jd(request.title, request.description)

        req_skills = list(set(analysis["required_skills"]).union(set(request.must_have_skills)))
        pref_skills = list(set(analysis["preferred_skills"]).union(set(request.nice_to_have_skills)))
        pref_skills = [s for s in pref_skills if s not in req_skills]

        job_id = db.add_job(
            title=request.title,
            description=request.description,
            role_family=request.role_family or analysis["role"],
            experience_required=analysis["experience_required"],
            required_skills=sorted(req_skills),
            preferred_skills=sorted(pref_skills)
        )

        saved_job = db.get_job(job_id)
        if not saved_job:
            raise HTTPException(status_code=500, detail="Failed to save and retrieve job.")

        return JobResponse(**saved_job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

@router.get("", response_model=list[JobResponse])
def list_jobs():
    """List all active jobs stored in SQLite."""
    try:
        jobs = db.get_jobs()
        return [JobResponse(**j) for j in jobs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing jobs: {str(e)}")

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int):
    """Retrieve details for a single job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")
    return JobResponse(**job)

@router.post("/analyze-jd", response_model=JobAnalysisResult)
def parse_job_description(request: JobCreate):
    """Dry-run analysis of a job description to return extracted structured requirements."""
    try:
        analysis = analyze_jd(request.title, request.description)
        req_skills = list(set(analysis["required_skills"]).union(set(request.must_have_skills)))
        pref_skills = list(set(analysis["preferred_skills"]).union(set(request.nice_to_have_skills)))
        pref_skills = [s for s in pref_skills if s not in req_skills]

        return JobAnalysisResult(
            role=request.role_family or analysis["role"],
            experience=analysis["experience_required"],
            required_skills=sorted(req_skills),
            preferred_skills=sorted(pref_skills)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing job description: {str(e)}")

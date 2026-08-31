from fastapi import APIRouter, HTTPException, Response
from app.schemas.schemas import (
    ScreenRequest, MatchResultResponse, CompareResponse, DashboardMetricsResponse
)
from app.services.scoring_engine import calculate_score
from app.utils.pdf_generator import generate_candidate_pdf
from app.models import database as db

router = APIRouter(prefix="/v1/match", tags=["matching"])

@router.post("/screen", response_model=list[MatchResultResponse])
def screen_candidates(request: ScreenRequest):
    """Screen candidates for a job, calculating weighted matches and saving to SQLite."""
    job = db.get_job(request.job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {request.job_id} not found.")

    candidates = db.get_candidates_for_job(request.job_id)
    if not candidates:
        return []

    if request.candidate_ids:
        candidates = [c for c in candidates if c["id"] in request.candidate_ids]

    for cand in candidates:
        scores = calculate_score(cand, job)
        db.save_match_result(candidate_id=cand["id"], job_id=request.job_id, scores=scores)

    results = db.get_match_results_for_job(request.job_id)
    return [MatchResultResponse(**res) for res in results]

@router.get("/job/{job_id}", response_model=list[MatchResultResponse])
def get_leaderboard(job_id: int):
    """Retrieve ranked candidate match results for a job."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found.")

    results = db.get_match_results_for_job(job_id)
    return [MatchResultResponse(**res) for res in results]

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics():
    """Retrieve global dashboard KPI metrics."""
    try:
        metrics = db.get_dashboard_metrics()
        return DashboardMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/report/{candidate_id}")
def download_candidate_report(candidate_id: int):
    """Generate and export a PDF matching report for the candidate."""
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate with ID {candidate_id} not found.")

    job = db.get_job(candidate["job_id"])
    if not job:
        raise HTTPException(status_code=404, detail="Job linked to candidate not found.")

    match_res = db.get_match_result_by_candidate(candidate_id)
    if not match_res:
        match_res = calculate_score(candidate, job)

    try:
        pdf_bytes = generate_candidate_pdf(candidate, job, match_res)
        response = Response(content=pdf_bytes, media_type="application/pdf")
        response.headers["Content-Disposition"] = f"attachment; filename=Evaluation_{candidate['name'].replace(' ', '_')}.pdf"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/compare/{candidate_a_id}/{candidate_b_id}", response_model=CompareResponse)
def compare_candidates(candidate_a_id: int, candidate_b_id: int):
    """Compare two candidates side-by-side."""
    match_a = db.get_match_result_by_candidate(candidate_a_id)
    match_b = db.get_match_result_by_candidate(candidate_b_id)

    if not match_a or not match_b:
        raise HTTPException(status_code=404, detail="One or both candidates have not been screened yet.")

    cand_a = db.get_candidate(candidate_a_id)
    cand_b = db.get_candidate(candidate_b_id)

    if cand_a:
        match_a["candidate_name"] = cand_a["name"]
        match_a["experience_years"] = cand_a["experience_years"]
    if cand_b:
        match_b["candidate_name"] = cand_b["name"]
        match_b["experience_years"] = cand_b["experience_years"]

    return CompareResponse(
        candidate_a=MatchResultResponse(**match_a),
        candidate_b=MatchResultResponse(**match_b)
    )

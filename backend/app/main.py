from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.models.database import init_db
from app.api.job_routes import router as job_router
from app.api.resume_routes import router as resume_router
from app.api.matching_routes import router as match_router
from app.web.routes import router as web_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="HireMatch AI - Screening & Ranking Engine",
    version="1.0.0",
    description="Explainable candidate-job matching engine using custom semantic matching, weighted scoring, and SQLite persistence.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="backend/app/web/static"), name="static")

app.include_router(web_router)
app.include_router(job_router)
app.include_router(resume_router)
app.include_router(match_router)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "app": "HireMatch AI"}

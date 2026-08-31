import sqlite3
import os
import json
from contextlib import contextmanager

DB_PATH = "hirematch.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    """Create database tables if they do not exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Jobs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                role_family TEXT NOT NULL,
                experience_required REAL DEFAULT 0,
                required_skills TEXT, -- JSON list
                preferred_skills TEXT, -- JSON list
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Candidates Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                experience_years REAL DEFAULT 0,
                skills TEXT, -- JSON list
                education TEXT, -- JSON list
                projects TEXT, -- JSON list
                resume_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        """)
        
        # Match Results Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS match_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                overall_score REAL DEFAULT 0,
                skill_score REAL DEFAULT 0,
                experience_score REAL DEFAULT 0,
                responsibility_score REAL DEFAULT 0,
                education_score REAL DEFAULT 0,
                semantic_score REAL DEFAULT 0,
                matched_skills TEXT, -- JSON list
                missing_skills TEXT, -- JSON list
                strengths TEXT, -- JSON list
                concerns TEXT, -- JSON list
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            )
        """)

def add_job(title: str, description: str, role_family: str, experience_required: float, required_skills: list, preferred_skills: list) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (title, description, role_family, experience_required, required_skills, preferred_skills)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                role_family,
                experience_required,
                json.dumps(required_skills),
                json.dumps(preferred_skills)
            )
        )
        return cursor.lastrowid

def get_jobs() -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY id DESC")
        rows = cursor.fetchall()
        jobs = []
        for r in rows:
            job = dict(r)
            job["required_skills"] = json.loads(job["required_skills"] or "[]")
            job["preferred_skills"] = json.loads(job["preferred_skills"] or "[]")
            jobs.append(job)
        return jobs

def get_job(job_id: int) -> dict | None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            return None
        job = dict(row)
        job["required_skills"] = json.loads(job["required_skills"] or "[]")
        job["preferred_skills"] = json.loads(job["preferred_skills"] or "[]")
        return job

def add_candidate(job_id: int, name: str, experience_years: float, skills: list, education: list, projects: list, resume_text: str) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO candidates (job_id, name, experience_years, skills, education, projects, resume_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                name,
                experience_years,
                json.dumps(skills),
                json.dumps(education),
                json.dumps(projects),
                resume_text
            )
        )
        return cursor.lastrowid

def get_candidates_for_job(job_id: int) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE job_id = ?", (job_id,))
        rows = cursor.fetchall()
        candidates = []
        for r in rows:
            cand = dict(r)
            cand["skills"] = json.loads(cand["skills"] or "[]")
            cand["education"] = json.loads(cand["education"] or "[]")
            cand["projects"] = json.loads(cand["projects"] or "[]")
            candidates.append(cand)
        return candidates

def get_candidate(candidate_id: int) -> dict | None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
        row = cursor.fetchone()
        if not row:
            return None
        cand = dict(row)
        cand["skills"] = json.loads(cand["skills"] or "[]")
        cand["education"] = json.loads(cand["education"] or "[]")
        cand["projects"] = json.loads(cand["projects"] or "[]")
        return cand

def save_match_result(candidate_id: int, job_id: int, scores: dict) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        # Delete existing match result if exists
        cursor.execute("DELETE FROM match_results WHERE candidate_id = ?", (candidate_id,))
        cursor.execute(
            """
            INSERT INTO match_results (
                candidate_id, job_id, overall_score, skill_score, experience_score,
                responsibility_score, education_score, semantic_score, matched_skills,
                missing_skills, strengths, concerns, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                job_id,
                scores["overall_score"],
                scores["skill_score"],
                scores["experience_score"],
                scores["responsibility_score"],
                scores["education_score"],
                scores["semantic_score"],
                json.dumps(scores["matched_skills"]),
                json.dumps(scores["missing_skills"]),
                json.dumps(scores["strengths"]),
                json.dumps(scores["concerns"]),
                scores["summary"]
            )
        )
        return cursor.lastrowid

def get_match_result_by_candidate(candidate_id: int) -> dict | None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM match_results WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["matched_skills"] = json.loads(res["matched_skills"] or "[]")
        res["missing_skills"] = json.loads(res["missing_skills"] or "[]")
        res["strengths"] = json.loads(res["strengths"] or "[]")
        res["concerns"] = json.loads(res["concerns"] or "[]")
        return res

def get_match_results_for_job(job_id: int) -> list[dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.*, c.name as candidate_name, c.experience_years, c.education, c.projects
            FROM match_results m
            JOIN candidates c ON m.candidate_id = c.id
            WHERE m.job_id = ?
            ORDER BY m.overall_score DESC
            """,
            (job_id,)
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            res = dict(r)
            res["matched_skills"] = json.loads(res["matched_skills"] or "[]")
            res["missing_skills"] = json.loads(res["missing_skills"] or "[]")
            res["strengths"] = json.loads(res["strengths"] or "[]")
            res["concerns"] = json.loads(res["concerns"] or "[]")
            res["education"] = json.loads(res["education"] or "[]")
            res["projects"] = json.loads(res["projects"] or "[]")
            results.append(res)
        return results

def get_dashboard_metrics() -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Active Jobs Count
        cursor.execute("SELECT COUNT(*) FROM jobs")
        active_jobs = cursor.fetchone()[0]
        
        # Candidates Count
        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]
        
        # Avg Match Score
        cursor.execute("SELECT AVG(overall_score) FROM match_results")
        avg_score_row = cursor.fetchone()[0]
        avg_match = round(avg_score_row, 1) if avg_score_row is not None else 0.0
        
        # Top Candidates Count (score >= 80.0)
        cursor.execute("SELECT COUNT(*) FROM match_results WHERE overall_score >= 80.0")
        top_candidates = cursor.fetchone()[0]
        
        return {
            "active_jobs": active_jobs,
            "total_candidates": total_candidates,
            "avg_match": avg_match,
            "top_candidates": top_candidates
        }

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from services.parser_service import ParserService
from services.ai_service import AIService
from services.chat_service import ChatService
from database import SessionLocal, engine, Base, get_db
import models
from pydantic import BaseModel
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Resume Parser API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser_service = ParserService()
ai_service = AIService()
chat_service = ChatService()

from datetime import datetime

# --- Pydantic Models ---
class JobCreate(BaseModel):
    title: str
    description: str

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    candidate_count: int = 0

    class Config:
        from_attributes = True

class CandidateSummary(BaseModel):
    id: int
    name: str
    email: str
    score: float
    created_at: datetime

    class Config:
        from_attributes = True

# --- Helper Functions ---
def validate_resume_content(text: str) -> tuple[bool, str]:
    if not text or len(text.strip()) < 10:
        return False, "The uploaded resume appears to be empty. Please upload a valid resume."
    
    words = text.split()
    if len(words) < 50:
        return False, "The uploaded resume is too short. Please upload a complete resume with at least 50 words."
    
    resume_keywords = [
        'education', 'skills', 'work', 'university', 'college',
        'degree', 'bachelor', 'master', 'job', 'position', 'role',
        'achievements', 'certification', 'training'
    ]
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in resume_keywords if keyword in text_lower)
    
    if keyword_count < 3:
        return False, "The uploaded file doesn't appear to be a valid resume. Please upload a proper resume document."
    
    return True, ""

def validate_jd_content(text: str) -> tuple[bool, str]:
    if not text or len(text.strip()) < 10:
        return False, "Job description is empty. Please paste a valid job description."
    
    alpha_chars = sum(c.isalpha() for c in text)
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    if total_chars > 0 and alpha_chars / total_chars < 0.7:
        return False, "The text appears to contain invalid characters. Please paste a proper job description."
    
    words = [w for w in text.split() if any(c.isalpha() for c in w)]
    if len(words) < 20:
        return False, "Job description is too short. Please paste a complete job description with at least 20 words."
    
    jd_keywords = [
        'requirements', 'qualifications', 'experience',
        'role', 'position', 'job', 'candidate', 'required',
        'must', 'should', 'knowledge', 'ability', 'work'
    ]
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in jd_keywords if keyword in text_lower)
    
    if keyword_count < 2:
        return False, "The text doesn't appear to be a valid job description. Please paste proper job description content with requirements and responsibilities."
    
    return True, ""

# --- Endpoints ---

class ChatRequest(BaseModel):
    message: str
    resume_text: str = ""
    jd_text: str = ""

@app.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Fetch Database Context
    jobs = db.query(models.Job).all()
    
    db_context_lines = []
    db_context_lines.append(f"Total Active Jobs: {len(jobs)}")
    
    for job in jobs:
        candidate_count = len(job.candidates)
        db_context_lines.append(f"- Job: {job.title} (ID: {job.id}) | Applicants: {candidate_count}")
        
        if candidate_count > 0:
            # Get top candidate
            top_candidate = max(job.candidates, key=lambda c: c.score)
            match_score = round(top_candidate.score * 10, 1) # Assuming score is 0-10 or 0-100 logic, user said "in radar visualization" usually 0-10 or 0-100. Let's just print raw for now or format.
            # actually score in models is float.
            
            # Construct link
            link = f"http://localhost:3000/dashboard/candidate/{top_candidate.id}"
            
            db_context_lines.append(f"  * Top Candidate: {top_candidate.name} (Score: {top_candidate.score})")
            db_context_lines.append(f"    - Link to Analysis: {link}")
    
    db_context = "\n".join(db_context_lines)

    result = await chat_service.get_response(request.message, request.resume_text, request.jd_text, db_context)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    jd_text: str = Form(...)
):
    try:
        resume_content = await resume.read()
        if len(resume_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Resume file is too large. Maximum size is 5MB.")
        
        resume_text = await parser_service.extract_text(resume.filename, resume_content)
        
        is_valid_resume, resume_error = validate_resume_content(resume_text)
        if not is_valid_resume:
            raise HTTPException(status_code=400, detail=resume_error)
        
        is_valid_jd, jd_error = validate_jd_content(jd_text)
        if not is_valid_jd:
            raise HTTPException(status_code=400, detail=jd_error)
        
        result = await ai_service.analyze_resume(resume_text, jd_text)
        result["resume_text"] = resume_text
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Recruitment Platform Endpoints ---

@app.post("/jobs", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = models.Job(title=job.title, description=job.description)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@app.get("/jobs", response_model=List[JobResponse])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    jobs = db.query(models.Job).offset(skip).limit(limit).all()
    for job in jobs:
        job.candidate_count = len(job.candidates)
    return jobs

@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    return {"message": "Job and associated candidates deleted successfully"}

@app.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.candidate_count = len(job.candidates)
    return job


@app.post("/jobs/{job_id}/apply")
async def apply_to_job(
    job_id: int,
    name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Check if job exists
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # 2. Extract Resume Text
    resume_content = await resume.read()
    if len(resume_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Resume file is too large. Maximum size is 5MB.")
    
    resume_text = await parser_service.extract_text(resume.filename, resume_content)
    
    is_valid_resume, resume_error = validate_resume_content(resume_text)
    if not is_valid_resume:
        raise HTTPException(status_code=400, detail=resume_error)

    # 3. Analyze against Job Description
    try:
        analysis_result = await ai_service.analyze_resume(resume_text, job.description)
        analysis_result["resume_text"] = resume_text
        analysis_result["jd_text"] = job.description # Include JD for context
        
        # 4. Save Candidate
        db_candidate = models.Candidate(
            name=name,
            email=email,
            resume_filename=resume.filename,
            score=analysis_result.get("similarity_score", 0),
            analysis_json=analysis_result,
            job_id=job_id
        )
        db.add(db_candidate)
        db.commit()
        db.refresh(db_candidate)
        
        return {"message": "Application submitted successfully", "candidate_id": db_candidate.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/jobs/{job_id}/candidates", response_model=List[CandidateSummary])
def read_candidates(job_id: int, db: Session = Depends(get_db)):
    return db.query(models.Candidate).filter(models.Candidate.job_id == job_id).order_by(models.Candidate.score.desc()).all()

@app.get("/candidates/{candidate_id}")
def read_candidate_analysis(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate.analysis_json

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

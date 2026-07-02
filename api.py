from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from models.schemas import AnalysisRequest, AnalysisResult, StoredAnalysis
from services.database_service import DatabaseService
from services.pdf_service import PDFExtractionError, PDFService
from services.report_service import ReportService
from services.scoring_service import ScoringService
from utils.config import MAX_UPLOAD_MB, REPORT_DIR, SUPPORTED_PDF_MIME_TYPES, UPLOAD_DIR, ensure_directories
from utils.logger import get_logger

ensure_directories()

app = FastAPI(
    title="AI Resume Analyzer API",
    description="Analyze PDF resumes against job descriptions and generate ATS improvement reports.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger("api")
pdf_service = PDFService()
scoring_service = ScoringService()
database_service = DatabaseService()
report_service = ReportService()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze/text", response_model=AnalysisResult)
def analyze_text(payload: AnalysisRequest) -> AnalysisResult:
    if not payload.resume_text.strip() or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Resume text and job description are required.")
    result = scoring_service.analyze(payload.resume_text, payload.job_description)
    database_service.save_analysis(result, payload.job_title)
    report_service.save_markdown_report(result, payload.job_title)
    return result


@app.post("/analyze/pdf", response_model=AnalysisResult)
async def analyze_pdf(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    job_title: str = Form("Untitled Role"),
) -> AnalysisResult:
    _validate_upload(resume)
    saved_path = _save_upload(resume)
    try:
        resume_text = pdf_service.extract_text(saved_path)
        result = scoring_service.analyze(resume_text, job_description)
        database_service.save_analysis(result, job_title)
        report_service.save_markdown_report(result, job_title)
        return result
    except PDFExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected analysis failure")
        raise HTTPException(status_code=500, detail="Analysis failed.") from exc


@app.get("/analyses", response_model=list[StoredAnalysis])
def list_analyses(limit: int = 25) -> list[StoredAnalysis]:
    return database_service.list_analyses(limit=limit)


@app.get("/reports/{filename}")
def download_report(filename: str) -> FileResponse:
    path = REPORT_DIR / filename
    if not path.exists() or path.suffix.lower() != ".md":
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(path, media_type="text/markdown", filename=path.name)


def _validate_upload(upload: UploadFile) -> None:
    if upload.content_type not in SUPPORTED_PDF_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
    size = upload.size or 0
    if size > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File must be smaller than {MAX_UPLOAD_MB} MB.")


def _save_upload(upload: UploadFile) -> Path:
    filename = f"{uuid4().hex}_{Path(upload.filename or 'resume.pdf').name}"
    destination = UPLOAD_DIR / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    logger.info("Saved uploaded resume to %s", destination)
    return destination

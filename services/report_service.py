from __future__ import annotations

from datetime import datetime
from pathlib import Path

from models.schemas import AnalysisResult
from utils.config import REPORT_DIR, ensure_directories


class ReportService:
    def save_markdown_report(self, result: AnalysisResult, job_title: str) -> Path:
        ensure_directories()
        safe_title = "".join(char if char.isalnum() else "_" for char in job_title.lower()).strip("_")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = REPORT_DIR / f"{safe_title or 'analysis'}_{timestamp}.md"
        path.write_text(result.report, encoding="utf-8")
        return path

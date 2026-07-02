from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
STATIC_DIR = BASE_DIR / "static"
DATABASE_PATH = BASE_DIR / "database.db"

MAX_UPLOAD_MB = 10
SUPPORTED_PDF_MIME_TYPES = {"application/pdf"}

SKILL_ALIASES: dict[str, set[str]] = {
    "python": {"python", "python3"},
    "sql": {"sql", "sqlite", "postgresql", "mysql", "t-sql"},
    "machine learning": {"machine learning", "ml", "scikit-learn", "sklearn"},
    "deep learning": {"deep learning", "neural networks", "pytorch", "tensorflow", "keras"},
    "nlp": {"nlp", "natural language processing", "spacy", "transformers"},
    "data analysis": {"data analysis", "analytics", "pandas", "numpy"},
    "visualization": {"visualization", "matplotlib", "seaborn", "plotly", "power bi", "tableau"},
    "fastapi": {"fastapi"},
    "streamlit": {"streamlit"},
    "django": {"django"},
    "flask": {"flask"},
    "aws": {"aws", "amazon web services"},
    "azure": {"azure"},
    "gcp": {"gcp", "google cloud"},
    "docker": {"docker", "containerization"},
    "kubernetes": {"kubernetes", "k8s"},
    "git": {"git", "github", "gitlab"},
    "linux": {"linux", "unix", "bash"},
    "rest api": {"rest api", "restful", "api development"},
    "javascript": {"javascript", "js", "typescript", "ts"},
    "react": {"react", "react.js", "next.js"},
    "communication": {"communication", "stakeholder management"},
    "leadership": {"leadership", "team lead", "mentoring"},
    "project management": {"project management", "agile", "scrum", "jira"},
}


def ensure_directories() -> None:
    for directory in (UPLOAD_DIR, REPORT_DIR, STATIC_DIR):
        directory.mkdir(parents=True, exist_ok=True)

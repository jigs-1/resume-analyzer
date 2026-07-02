from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResumeSections(BaseModel):
    skills: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class JobDescription(BaseModel):
    title: str = "Untitled Role"
    description: str
    required_skills: list[str] = Field(default_factory=list)


class AnalysisRequest(BaseModel):
    resume_text: str
    job_description: str
    job_title: str = "Untitled Role"


class AnalysisResult(BaseModel):
    ats_score: int
    matching_percentage: float
    semantic_similarity: float
    matched_skills: list[str]
    missing_skills: list[str]
    resume_sections: ResumeSections
    recommendations: list[str]
    report: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_record(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class StoredAnalysis(BaseModel):
    id: int
    job_title: str
    ats_score: int
    matching_percentage: float
    missing_skills: list[str]
    created_at: datetime

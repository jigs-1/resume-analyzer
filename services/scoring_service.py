from __future__ import annotations

from models.schemas import AnalysisResult, ResumeSections
from services.nlp_service import NLPService
from services.transformer_service import TransformerService
from utils.text import normalize_skill, word_count


class ScoringService:
    def __init__(self, nlp_service: NLPService | None = None, transformer_service: TransformerService | None = None) -> None:
        self.nlp_service = nlp_service or NLPService()
        self.transformer_service = transformer_service or TransformerService()

    def analyze(self, resume_text: str, job_description: str) -> AnalysisResult:
        sections = self.nlp_service.extract_resume_sections(resume_text)
        resume_skills = {normalize_skill(skill) for skill in sections.skills}
        required_skills = self.nlp_service.extract_required_skills(job_description)
        required_skill_set = {normalize_skill(skill) for skill in required_skills}

        matched = sorted(required_skill_set & resume_skills)
        missing = sorted(required_skill_set - resume_skills)
        skill_score = len(matched) / len(required_skill_set) if required_skill_set else 0.0
        semantic_score = self.transformer_service.semantic_similarity(resume_text, job_description)
        structure_score = self._structure_score(sections)
        content_depth_score = self._content_depth_score(resume_text)

        ats_score = round(
            (skill_score * 0.45 + semantic_score * 0.35 + structure_score * 0.12 + content_depth_score * 0.08) * 100
        )
        ats_score = max(0, min(100, ats_score))
        matching_percentage = round((skill_score * 0.6 + semantic_score * 0.4) * 100, 2)

        recommendations = self._recommendations(sections, missing, ats_score, content_depth_score)
        report = self._build_report(
            ats_score=ats_score,
            matching_percentage=matching_percentage,
            semantic_similarity=semantic_score,
            matched_skills=matched,
            missing_skills=missing,
            recommendations=recommendations,
        )

        return AnalysisResult(
            ats_score=ats_score,
            matching_percentage=matching_percentage,
            semantic_similarity=round(semantic_score * 100, 2),
            matched_skills=[skill.title() for skill in matched],
            missing_skills=[skill.title() for skill in missing],
            resume_sections=sections,
            recommendations=recommendations,
            report=report,
        )

    def _structure_score(self, sections: ResumeSections) -> float:
        available = sum(
            1 for values in (
                sections.skills,
                sections.education,
                sections.experience,
                sections.projects,
                sections.certifications,
            )
            if values
        )
        return available / 5

    def _content_depth_score(self, resume_text: str) -> float:
        count = word_count(resume_text)
        if count >= 550:
            return 1.0
        if count <= 120:
            return 0.25
        return count / 550

    def _recommendations(
        self,
        sections: ResumeSections,
        missing_skills: list[str],
        ats_score: int,
        content_depth_score: float,
    ) -> list[str]:
        recommendations: list[str] = []
        if missing_skills:
            top_missing = ", ".join(skill.title() for skill in missing_skills[:8])
            recommendations.append(f"Add credible evidence for missing role skills: {top_missing}.")
        if not sections.projects:
            recommendations.append("Add a projects section with problem, tools, outcome, and measurable impact.")
        if not sections.certifications:
            recommendations.append("Include relevant certifications or training if they strengthen the target role fit.")
        if content_depth_score < 0.6:
            recommendations.append("Expand brief bullets with scope, action verbs, tools used, and quantified outcomes.")
        if ats_score < 70:
            recommendations.append("Mirror important job description keywords naturally in your skills and experience sections.")
        if not recommendations:
            recommendations.append("Resume is well aligned. Fine tune bullets for measurable impact and role-specific keywords.")
        return recommendations

    def _build_report(
        self,
        ats_score: int,
        matching_percentage: float,
        semantic_similarity: float,
        matched_skills: list[str],
        missing_skills: list[str],
        recommendations: list[str],
    ) -> str:
        lines = [
            "# Resume Improvement Report",
            "",
            f"ATS Score: {ats_score}/100",
            f"Matching Percentage: {matching_percentage}%",
            f"Semantic Similarity: {round(semantic_similarity * 100, 2)}%",
            "",
            "## Matched Skills",
            ", ".join(skill.title() for skill in matched_skills) or "No direct skill matches found.",
            "",
            "## Missing Skills",
            ", ".join(skill.title() for skill in missing_skills) or "No major missing skills detected.",
            "",
            "## Recommendations",
            *[f"- {recommendation}" for recommendation in recommendations],
        ]
        return "\n".join(lines)

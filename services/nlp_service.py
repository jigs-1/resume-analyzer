from __future__ import annotations

import re
from functools import cached_property

import spacy
from spacy.language import Language

from models.schemas import ResumeSections
from utils.config import SKILL_ALIASES
from utils.logger import get_logger
from utils.text import SECTION_HEADERS, normalize_skill, sentence_split, unique_preserve_order


class NLPService:
    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    @cached_property
    def nlp(self) -> Language:
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model en_core_web_sm not found. Falling back to blank English pipeline.")
            return spacy.blank("en")

    def extract_resume_sections(self, text: str) -> ResumeSections:
        sections = self._split_sections(text)
        return ResumeSections(
            skills=self.extract_skills(sections.get("skills", text)),
            education=self._extract_lines(sections.get("education") or text, fallback_patterns=("degree", "university", "college")),
            experience=self._extract_lines(sections.get("experience") or text, fallback_patterns=("engineer", "developer", "analyst", "manager")),
            projects=self._extract_lines(sections.get("projects") or text, fallback_patterns=("built", "developed", "implemented")),
            certifications=self._extract_lines(sections.get("certifications") or text, fallback_patterns=("certified", "certificate", "certification")),
        )

    def extract_skills(self, text: str) -> list[str]:
        lowered = text.lower()
        matched: list[str] = []
        for canonical, aliases in SKILL_ALIASES.items():
            if any(self._contains_term(lowered, alias) for alias in aliases):
                matched.append(canonical.title() if len(canonical) > 3 else canonical.upper())

        noun_chunks = self._safe_noun_chunks(text)
        technical_terms = [
            chunk for chunk in noun_chunks
            if 2 <= len(chunk) <= 35 and re.search(r"[A-Za-z]", chunk)
        ]
        return unique_preserve_order([*matched, *technical_terms])[:40]

    def extract_required_skills(self, job_description: str) -> list[str]:
        skills = self.extract_skills(job_description)
        requirement_sentences = [
            sentence for sentence in sentence_split(job_description)
            if re.search(r"\b(required|must|proficient|experience with|knowledge of|skills)\b", sentence, re.I)
        ]
        extras = self.extract_skills("\n".join(requirement_sentences)) if requirement_sentences else []
        return unique_preserve_order([*extras, *skills])[:35]

    def _split_sections(self, text: str) -> dict[str, str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        current = "summary"
        sections: dict[str, list[str]] = {current: []}

        for line in lines:
            normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
            matched_section = self._header_to_section(normalized)
            if matched_section:
                current = matched_section
                sections.setdefault(current, [])
                continue
            sections.setdefault(current, []).append(line)

        return {key: "\n".join(value).strip() for key, value in sections.items()}

    def _header_to_section(self, header: str) -> str | None:
        for section, aliases in SECTION_HEADERS.items():
            if header in aliases:
                return section
        return None

    def _extract_lines(self, text: str, fallback_patterns: tuple[str, ...]) -> list[str]:
        lines = [line.strip(" -•\t") for line in text.splitlines() if len(line.strip()) > 3]
        if lines:
            return unique_preserve_order(lines)[:12]
        sentences = [
            sentence for sentence in sentence_split(text)
            if any(pattern in sentence.lower() for pattern in fallback_patterns)
        ]
        return unique_preserve_order(sentences)[:12]

    def _safe_noun_chunks(self, text: str) -> list[str]:
        doc = self.nlp(text[:100_000])
        if "parser" not in self.nlp.pipe_names:
            return []
        return [chunk.text.strip() for chunk in doc.noun_chunks]

    def _contains_term(self, text: str, term: str) -> bool:
        escaped = re.escape(normalize_skill(term))
        return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text))

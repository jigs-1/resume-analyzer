from __future__ import annotations

import re
from collections.abc import Iterable


SECTION_HEADERS = {
    "skills": ("skills", "technical skills", "core competencies", "technologies"),
    "education": ("education", "academic background", "qualification", "qualifications"),
    "experience": ("experience", "work experience", "professional experience", "employment"),
    "projects": ("projects", "selected projects", "academic projects", "portfolio"),
    "certifications": ("certifications", "certificates", "licenses", "training"),
}


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip().lower())


def unique_preserve_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        clean = item.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            output.append(clean)
    return output


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [part.strip(" -•\t") for part in parts if part.strip(" -•\t")]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w.+#-]+\b", text.lower()))

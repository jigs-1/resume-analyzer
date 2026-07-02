from __future__ import annotations

from pathlib import Path

import pdfplumber

from utils.logger import get_logger
from utils.text import normalize_text


class PDFExtractionError(RuntimeError):
    pass


class PDFService:
    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    def extract_text(self, file_path: str | Path) -> str:
        path = Path(file_path)
        if not path.exists():
            raise PDFExtractionError(f"PDF not found: {path}")
        if path.suffix.lower() != ".pdf":
            raise PDFExtractionError("Only PDF files are supported.")

        try:
            pages: list[str] = []
            with pdfplumber.open(path) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    self.logger.info("Extracted %s characters from page %s", len(page_text), index)
                    pages.append(page_text)
            text = normalize_text("\n".join(pages))
        except Exception as exc:
            self.logger.exception("PDF extraction failed for %s", path)
            raise PDFExtractionError("Unable to extract text from the PDF.") from exc

        if not text:
            raise PDFExtractionError("No readable text found in this PDF.")
        return text

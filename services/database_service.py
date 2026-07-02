from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from models.schemas import AnalysisResult, StoredAnalysis
from utils.config import DATABASE_PATH
from utils.logger import get_logger


class DatabaseService:
    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.logger = get_logger(self.__class__.__name__)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_title TEXT NOT NULL,
                    ats_score INTEGER NOT NULL,
                    matching_percentage REAL NOT NULL,
                    semantic_similarity REAL NOT NULL,
                    matched_skills TEXT NOT NULL,
                    missing_skills TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    report TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_analysis(self, result: AnalysisResult, job_title: str) -> int:
        with self.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analyses (
                    job_title, ats_score, matching_percentage, semantic_similarity,
                    matched_skills, missing_skills, recommendations, report, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_title,
                    result.ats_score,
                    result.matching_percentage,
                    result.semantic_similarity,
                    json.dumps(result.matched_skills),
                    json.dumps(result.missing_skills),
                    json.dumps(result.recommendations),
                    result.report,
                    result.created_at.isoformat(),
                ),
            )
            analysis_id = int(cursor.lastrowid)
            self.logger.info("Saved analysis %s for %s", analysis_id, job_title)
            return analysis_id

    def list_analyses(self, limit: int = 25) -> list[StoredAnalysis]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT id, job_title, ats_score, matching_percentage, missing_skills, created_at
                FROM analyses
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            StoredAnalysis(
                id=row["id"],
                job_title=row["job_title"],
                ats_score=row["ats_score"],
                matching_percentage=row["matching_percentage"],
                missing_skills=json.loads(row["missing_skills"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

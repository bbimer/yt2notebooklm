"""SQLite database operations and schema management."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from research_academy.models import (
    ClaimModel,
    DiscoveryStatus,
    GatekeeperEvaluation,
    MethodistAnalysis,
    TranscriptSegment,
    VideoMetadata,
    VideoTranscript,
    WebDocumentMetadata,
    utc_now,
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    channel_id TEXT NOT NULL,
    channel_title TEXT NOT NULL,
    published_at TEXT,
    duration_seconds INTEGER DEFAULT 0,
    view_count INTEGER,
    like_count INTEGER,
    channel_follower_count INTEGER,
    url TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    domain TEXT DEFAULT 'crypto',
    language TEXT,
    like_ratio REAL,
    views_to_subscribers_ratio REAL,
    discovery_status TEXT NOT NULL,
    status_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL DEFAULT 'crypto',
    topic_id TEXT NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    author_or_domain TEXT,
    published_at TEXT,
    clean_markdown TEXT NOT NULL,
    outline_json TEXT,
    word_count INTEGER NOT NULL,
    discovery_status TEXT NOT NULL,
    status_reason TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_topic ON documents(topic_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(discovery_status);
CREATE INDEX IF NOT EXISTS idx_documents_domain ON documents(domain);

CREATE TABLE IF NOT EXISTS video_queries (
    video_id TEXT NOT NULL,
    query TEXT NOT NULL,
    PRIMARY KEY (video_id, query),
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transcripts (
    video_id TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    full_raw_text TEXT NOT NULL,
    full_normalized_text TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    has_subtitles INTEGER NOT NULL DEFAULT 1,
    source_type TEXT NOT NULL,
    fetch_status TEXT NOT NULL,
    error_message TEXT,
    fetched_at TEXT NOT NULL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS transcript_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    start_seconds REAL NOT NULL,
    end_seconds REAL NOT NULL,
    text TEXT NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'raw',
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    pass_type TEXT NOT NULL,
    relevance_score REAL,
    technical_depth_score REAL,
    practical_value_score REAL,
    source_quality_score REAL,
    commercial_noise_score REAL,
    decision TEXT NOT NULL,
    reasons_json TEXT,
    analysis_json TEXT,
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    statement TEXT NOT NULL,
    timestamp_seconds REAL,
    timestamp_formatted TEXT,
    independent_evidence TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    allowed_sales_phrasing TEXT,
    verified_at TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    pass_type TEXT NOT NULL,
    relevance_score REAL,
    technical_depth_score REAL,
    practical_value_score REAL,
    source_quality_score REAL,
    commercial_noise_score REAL,
    decision TEXT NOT NULL,
    reasons_json TEXT,
    analysis_json TEXT,
    evaluated_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    statement TEXT NOT NULL,
    anchor_id TEXT,
    independent_evidence TEXT,
    verification_status TEXT NOT NULL DEFAULT 'unverified',
    allowed_sales_phrasing TEXT,
    verified_at TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(document_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS jobs_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type TEXT NOT NULL,
    topic_id TEXT,
    status TEXT NOT NULL,
    details_json TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_videos_topic ON videos(topic_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(discovery_status);
CREATE INDEX IF NOT EXISTS idx_evaluations_video ON evaluations(video_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(verification_status);
CREATE INDEX IF NOT EXISTS idx_doc_evaluations_doc ON document_evaluations(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_claims_doc ON document_claims(document_id);
"""


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            # Safe non-breaking migration for domain column in videos
            cur = conn.execute("PRAGMA table_info(videos);")
            columns = [r["name"] for r in cur.fetchall()]
            if "domain" not in columns:
                conn.execute("ALTER TABLE videos ADD COLUMN domain TEXT DEFAULT 'crypto';")

    # --- Videos & Deduplication ---

    def upsert_video(self, video: VideoMetadata, query_matched: Optional[str] = None) -> bool:
        """
        Inserts or updates video metadata.
        Returns True if newly inserted, False if already existed.
        """
        now_str = utc_now().isoformat()
        domain = getattr(video, "domain", "crypto") or "crypto"
        with self.get_connection() as conn:
            cur = conn.execute("SELECT video_id, discovery_status FROM videos WHERE video_id = ?", (video.video_id,))
            row = cur.fetchone()
            is_new = row is None

            if is_new:
                conn.execute(
                    """
                    INSERT INTO videos (
                        video_id, title, description, channel_id, channel_title,
                        published_at, duration_seconds, view_count, like_count,
                        channel_follower_count, url, topic_id, domain, language,
                        like_ratio, views_to_subscribers_ratio, discovery_status,
                        status_reason, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        video.video_id,
                        video.title,
                        video.description,
                        video.channel_id,
                        video.channel_title,
                        video.published_at.isoformat() if video.published_at else None,
                        video.duration_seconds,
                        video.view_count,
                        video.like_count,
                        video.channel_follower_count,
                        video.url,
                        video.topic_id,
                        domain,
                        video.language,
                        video.like_ratio,
                        video.views_to_subscribers_ratio,
                        video.discovery_status.value,
                        video.status_reason,
                        now_str,
                        now_str,
                    ),
                )
            else:
                # Update stats only, preserve published or reviewed status unless retry requested
                conn.execute(
                    """
                    UPDATE videos SET
                        view_count = COALESCE(?, view_count),
                        like_count = COALESCE(?, like_count),
                        like_ratio = COALESCE(?, like_ratio),
                        views_to_subscribers_ratio = COALESCE(?, views_to_subscribers_ratio),
                        updated_at = ?
                    WHERE video_id = ?
                    """,
                    (
                        video.view_count,
                        video.like_count,
                        video.like_ratio,
                        video.views_to_subscribers_ratio,
                        now_str,
                        video.video_id,
                    ),
                )

            # Record search query match
            query_to_add = query_matched or (video.queries_matched[0] if video.queries_matched else None)
            if query_to_add:
                conn.execute(
                    "INSERT OR IGNORE INTO video_queries (video_id, query) VALUES (?, ?)",
                    (video.video_id, query_to_add),
                )

            return is_new

    def get_video(self, video_id: str) -> Optional[VideoMetadata]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            # Fetch queries
            q_cur = conn.execute("SELECT query FROM video_queries WHERE video_id = ?", (video_id,))
            queries = [r["query"] for r in q_cur.fetchall()]
            data["queries_matched"] = queries
            if data.get("published_at"):
                data["published_at"] = datetime.fromisoformat(data["published_at"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            return VideoMetadata.model_validate(data)

    def list_videos(
        self,
        topic_id: Optional[str] = None,
        status: Optional[DiscoveryStatus] = None,
        limit: int = 100,
    ) -> List[VideoMetadata]:
        query = "SELECT * FROM videos WHERE 1=1"
        params: List[Any] = []
        if topic_id:
            query += " AND topic_id = ?"
            params.append(topic_id)
        if status:
            query += " AND discovery_status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cur = conn.execute(query, params)
            videos = []
            for row in cur.fetchall():
                data = dict(row)
                # Fetch matched queries
                q_cur = conn.execute(
                    "SELECT query FROM video_queries WHERE video_id = ?",
                    (data["video_id"],),
                )
                data["queries_matched"] = [r["query"] for r in q_cur.fetchall()]
                if data.get("published_at"):
                    data["published_at"] = datetime.fromisoformat(data["published_at"])
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                videos.append(VideoMetadata.model_validate(data))
            return videos

    def update_video_status(
        self, video_id: str, status: DiscoveryStatus, reason: Optional[str] = None
    ) -> None:
        now_str = utc_now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE videos SET
                    discovery_status = ?,
                    status_reason = ?,
                    updated_at = ?
                WHERE video_id = ?
                """,
                (status.value, reason, now_str, video_id),
            )

    # --- Transcripts ---

    def save_transcript(self, transcript: VideoTranscript) -> None:
        now_str = utc_now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO transcripts (
                    video_id, language, full_raw_text, full_normalized_text,
                    word_count, has_subtitles, source_type, fetch_status,
                    error_message, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript.video_id,
                    transcript.language,
                    transcript.full_raw_text,
                    transcript.full_normalized_text,
                    transcript.word_count,
                    1 if transcript.has_subtitles else 0,
                    transcript.segments[0].source_type if transcript.segments else "unknown",
                    transcript.fetch_status,
                    transcript.error_message,
                    now_str,
                ),
            )
            # Remove old segments and replace
            conn.execute("DELETE FROM transcript_segments WHERE video_id = ?", (transcript.video_id,))
            for seg in transcript.segments:
                conn.execute(
                    """
                    INSERT INTO transcript_segments (
                        video_id, start_seconds, end_seconds, text, quality_status
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        transcript.video_id,
                        seg.start_seconds,
                        seg.end_seconds,
                        seg.text,
                        seg.quality_status,
                    ),
                )

    def get_transcript(self, video_id: str) -> Optional[VideoTranscript]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM transcripts WHERE video_id = ?", (video_id,))
            row = cur.fetchone()
            if not row:
                return None
            seg_cur = conn.execute(
                "SELECT start_seconds, end_seconds, text, quality_status FROM transcript_segments WHERE video_id = ? ORDER BY start_seconds ASC",
                (video_id,),
            )
            segments = [
                TranscriptSegment(
                    start_seconds=r["start_seconds"],
                    end_seconds=r["end_seconds"],
                    text=r["text"],
                    language=row["language"],
                    source_type=row["source_type"],
                    quality_status=r["quality_status"],
                )
                for r in seg_cur.fetchall()
            ]
            return VideoTranscript(
                video_id=video_id,
                language=row["language"],
                segments=segments,
                full_raw_text=row["full_raw_text"],
                full_normalized_text=row["full_normalized_text"],
                word_count=row["word_count"],
                has_subtitles=bool(row["has_subtitles"]),
                fetch_status=row["fetch_status"],
                error_message=row["error_message"],
            )

    # --- Evaluations ---

    def save_gatekeeper_evaluation(
        self, source_id: str, eval_res: GatekeeperEvaluation
    ) -> None:
        now_str = utc_now().isoformat()
        is_document = self.get_document(source_id) is not None
        table_name = "document_evaluations" if is_document else "evaluations"
        id_col = "document_id" if is_document else "video_id"

        with self.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {table_name} (
                    {id_col}, pass_type, relevance_score, technical_depth_score,
                    practical_value_score, source_quality_score, commercial_noise_score,
                    decision, reasons_json, evaluated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    "gatekeeper",
                    eval_res.relevance_score,
                    eval_res.technical_depth_score,
                    eval_res.practical_value_score,
                    eval_res.source_quality_score,
                    eval_res.commercial_noise_score,
                    eval_res.decision.value,
                    json.dumps(eval_res.reasons, ensure_ascii=False),
                    now_str,
                ),
            )

    def save_methodist_analysis(
        self, source_id: str, analysis: MethodistAnalysis
    ) -> None:
        now_str = utc_now().isoformat()
        is_document = self.get_document(source_id) is not None
        eval_table = "document_evaluations" if is_document else "evaluations"
        id_col = "document_id" if is_document else "video_id"

        with self.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {eval_table} (
                    {id_col}, pass_type, decision, analysis_json, evaluated_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    "methodist",
                    "ACCEPTED",
                    analysis.model_dump_json(),
                    now_str,
                ),
            )
            # Save claims
            if is_document:
                for claim in analysis.key_claims:
                    conn.execute(
                        """
                        INSERT INTO document_claims (
                            document_id, claim_type, statement, anchor_id,
                            independent_evidence, verification_status,
                            allowed_sales_phrasing, verified_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            source_id,
                            claim.claim_type.value,
                            claim.statement,
                            claim.anchor_id or claim.timestamp_formatted,
                            claim.independent_evidence,
                            claim.verification_status,
                            claim.allowed_sales_phrasing,
                            now_str,
                        ),
                    )
            else:
                for claim in analysis.key_claims:
                    conn.execute(
                        """
                        INSERT INTO claims (
                            video_id, claim_type, statement, timestamp_seconds,
                            timestamp_formatted, independent_evidence,
                            verification_status, allowed_sales_phrasing, verified_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            source_id,
                            claim.claim_type.value,
                            claim.statement,
                            claim.timestamp_seconds,
                            claim.timestamp_formatted,
                            claim.independent_evidence,
                            claim.verification_status,
                            claim.allowed_sales_phrasing,
                            now_str,
                        ),
                    )

    def get_latest_evaluation(self, source_id: str, pass_type: str = "gatekeeper") -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM evaluations WHERE video_id = ? AND pass_type = ? ORDER BY id DESC LIMIT 1",
                (source_id, pass_type),
            )
            row = cur.fetchone()
            if row:
                return dict(row)
            # Fallback to document_evaluations
            cur = conn.execute(
                "SELECT * FROM document_evaluations WHERE document_id = ? AND pass_type = ? ORDER BY id DESC LIMIT 1",
                (source_id, pass_type),
            )
            row = cur.fetchone()
            return dict(row) if row else None

    # --- Jobs Log ---

    def start_job(self, job_type: str, topic_id: Optional[str] = None) -> int:
        now_str = utc_now().isoformat()
        with self.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO jobs_log (job_type, topic_id, status, started_at) VALUES (?, ?, ?, ?)",
                (job_type, topic_id, "RUNNING", now_str),
            )
            return cur.lastrowid

    def finish_job(self, job_id: int, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        now_str = utc_now().isoformat()
        details_str = json.dumps(details or {}, ensure_ascii=False)
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE jobs_log SET status = ?, details_json = ?, finished_at = ? WHERE id = ?",
                (status, details_str, now_str, job_id),
            )

    # --- Documents (Web Sources) ---

    def upsert_document(self, doc: WebDocumentMetadata) -> bool:
        """
        Inserts or updates web document metadata.
        Returns True if newly inserted, False if updated.
        """
        now_str = utc_now().isoformat()
        with self.get_connection() as conn:
            cur = conn.execute("SELECT document_id, discovery_status FROM documents WHERE document_id = ?", (doc.document_id,))
            row = cur.fetchone()
            is_new = row is None

            if is_new:
                conn.execute(
                    """
                    INSERT INTO documents (
                        document_id, domain, topic_id, url, title, author_or_domain,
                        published_at, clean_markdown, outline_json, word_count,
                        discovery_status, status_reason, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        doc.document_id,
                        doc.domain,
                        doc.topic_id,
                        doc.url,
                        doc.title,
                        doc.author_or_domain,
                        doc.published_at.isoformat() if doc.published_at else None,
                        doc.clean_markdown,
                        doc.outline_json,
                        doc.word_count,
                        doc.discovery_status.value,
                        doc.status_reason,
                        now_str,
                        now_str,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE documents SET
                        title = ?,
                        author_or_domain = ?,
                        clean_markdown = ?,
                        outline_json = ?,
                        word_count = ?,
                        discovery_status = ?,
                        status_reason = ?,
                        updated_at = ?
                    WHERE document_id = ?
                    """,
                    (
                        doc.title,
                        doc.author_or_domain,
                        doc.clean_markdown,
                        doc.outline_json,
                        doc.word_count,
                        doc.discovery_status.value,
                        doc.status_reason,
                        now_str,
                        doc.document_id,
                    ),
                )
            return is_new

    def get_document(self, document_id: str) -> Optional[WebDocumentMetadata]:
        with self.get_connection() as conn:
            cur = conn.execute("SELECT * FROM documents WHERE document_id = ?", (document_id,))
            row = cur.fetchone()
            if not row:
                return None
            data = dict(row)
            if data.get("published_at"):
                data["published_at"] = datetime.fromisoformat(data["published_at"])
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
            return WebDocumentMetadata.model_validate(data)

    def list_documents(
        self,
        domain: Optional[str] = None,
        topic_id: Optional[str] = None,
        status: Optional[DiscoveryStatus] = None,
        limit: int = 100,
    ) -> List[WebDocumentMetadata]:
        query = "SELECT * FROM documents WHERE 1=1"
        params: List[Any] = []
        if domain:
            query += " AND domain = ?"
            params.append(domain)
        if topic_id:
            query += " AND topic_id = ?"
            params.append(topic_id)
        if status:
            query += " AND discovery_status = ?"
            params.append(status.value)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.get_connection() as conn:
            cur = conn.execute(query, params)
            docs = []
            for row in cur.fetchall():
                data = dict(row)
                if data.get("published_at"):
                    data["published_at"] = datetime.fromisoformat(data["published_at"])
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["updated_at"] = datetime.fromisoformat(data["updated_at"])
                docs.append(WebDocumentMetadata.model_validate(data))
            return docs

    def update_document_status(
        self, document_id: str, status: DiscoveryStatus, reason: Optional[str] = None
    ) -> None:
        now_str = utc_now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                UPDATE documents SET
                    discovery_status = ?,
                    status_reason = ?,
                    updated_at = ?
                WHERE document_id = ?
                """,
                (status.value, reason, now_str, document_id),
            )

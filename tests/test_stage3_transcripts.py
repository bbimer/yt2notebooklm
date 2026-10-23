"""Tests for Stage 3: Transcripts, Normalization, Timestamps, and Fallbacks."""

from pathlib import Path
import pytest
from research_academy.config import AppConfig, ScoringSettings
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, TranscriptSegment, VideoMetadata, VideoTranscript
from research_academy.pipeline.normalization import normalize_caption_text
from research_academy.pipeline.transcription import TranscriptionPipeline
from research_academy.providers.base import TranscriptProvider


class MockTranscriptProvider(TranscriptProvider):
    def __init__(self, transcripts_map=None):
        self.transcripts_map = transcripts_map or {}

    def get_transcript(self, video_id: str, languages=None) -> VideoTranscript:
        if video_id in self.transcripts_map:
            return self.transcripts_map[video_id]
        return VideoTranscript(
            video_id=video_id,
            language="en",
            has_subtitles=False,
            fetch_status="NOT_FOUND",
            error_message="Subtitles not found in test mock",
        )


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_normalization_crypto_slang():
    raw_text = "we trade on buy bit and observe a mm liquidity pull with high sleep page"
    normalized = normalize_caption_text(raw_text)
    assert "Bybit" in normalized
    assert "AMM" in normalized
    assert "liquidity pool" in normalized
    assert "slippage" in normalized


def test_timestamps_formatting():
    seg1 = TranscriptSegment(start_seconds=75.4, end_seconds=82.1, text="Analyzing funding rates")
    assert seg1.timestamp_formatted == "01:15"

    seg2 = TranscriptSegment(start_seconds=3665.0, end_seconds=3670.0, text="Final conclusion")
    # 3665s = 61 mins 5 sec
    assert seg2.timestamp_formatted == "61:05"


def test_transcription_pipeline_success(temp_db: Database, tmp_path: Path):
    video = VideoMetadata(
        video_id="vid_trans_success",
        title="Funding Rate Arbitrage Trade",
        channel_id="chan_quant",
        channel_title="Quant Desk",
        url="https://youtube.com/watch?v=vid_trans_success",
        topic_id="funding-rate-arbitrage",
        duration_seconds=900,
    )
    temp_db.upsert_video(video)

    # 300 words to exceed minimum word count
    long_text = ("funding rate arbitrage perpetual futures delta neutral " * 50).strip()
    seg = TranscriptSegment(start_seconds=10.0, end_seconds=60.0, text=long_text)
    mock_transcript = VideoTranscript(
        video_id="vid_trans_success",
        language="en",
        segments=[seg],
        full_raw_text=long_text,
        full_normalized_text=long_text,
        word_count=len(long_text.split()),
        has_subtitles=True,
    )

    provider = MockTranscriptProvider({"vid_trans_success": mock_transcript})
    config = AppConfig(
        project_root=tmp_path,
        database_path=temp_db.db_path,
        scoring=ScoringSettings(),
    )
    pipeline = TranscriptionPipeline(config, temp_db, transcript_provider=provider)

    res = pipeline.process_video_transcript(video)
    assert res is not None
    assert res.word_count == 350

    db_video = temp_db.get_video("vid_trans_success")
    assert db_video.discovery_status == DiscoveryStatus.TRANSCRIPT_FETCHED


def test_transcription_pipeline_missing_subtitles(temp_db: Database, tmp_path: Path):
    video = VideoMetadata(
        video_id="vid_no_subs",
        title="Video Without Subtitles",
        channel_id="chan_silent",
        channel_title="No Subs Channel",
        url="https://youtube.com/watch?v=vid_no_subs",
        topic_id="funding-rate-arbitrage",
        duration_seconds=900,
    )
    temp_db.upsert_video(video)

    provider = MockTranscriptProvider({})
    config = AppConfig(
        project_root=tmp_path,
        database_path=temp_db.db_path,
        scoring=ScoringSettings(),
    )
    pipeline = TranscriptionPipeline(config, temp_db, transcript_provider=provider)

    res = pipeline.process_video_transcript(video)
    assert res is None

    db_video = temp_db.get_video("vid_no_subs")
    assert db_video.discovery_status == DiscoveryStatus.TRANSCRIPT_FAILED
    assert "Subtitles not found" in db_video.status_reason

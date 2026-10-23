"""Unit tests for models, config, and database operations."""

from datetime import datetime
from pathlib import Path
import pytest
from research_academy.config import get_config
from research_academy.database import Database
from research_academy.models import (
    DiscoveryStatus,
    GatekeeperEvaluation,
    GatekeeperVerdict,
    TranscriptSegment,
    VideoMetadata,
    VideoTranscript,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_video_metadata_derived_metrics():
    video = VideoMetadata(
        video_id="test12345",
        title="Funding Rate Arbitrage Deep Dive",
        channel_id="channel_1",
        channel_title="Quant Desk",
        url="https://youtube.com/watch?v=test12345",
        topic_id="funding-rate-arbitrage",
        view_count=10000,
        like_count=500,
        channel_follower_count=2000,
    )
    video.calculate_derived_metrics()
    assert video.like_ratio == 0.05
    assert video.views_to_subscribers_ratio == 5.0


def test_database_video_crud_and_deduplication(temp_db: Database):
    video1 = VideoMetadata(
        video_id="vid_abc",
        title="Order Book Dynamics",
        channel_id="chan_1",
        channel_title="Wintermute",
        url="https://youtube.com/watch?v=vid_abc",
        topic_id="market-microstructure",
        view_count=5000,
        like_count=250,
        duration_seconds=1200,
    )
    is_new = temp_db.upsert_video(video1, query_matched="order book microstructure")
    assert is_new is True

    # Same video found via another query
    is_new_again = temp_db.upsert_video(video1, query_matched="market makers crypto")
    assert is_new_again is False

    fetched = temp_db.get_video("vid_abc")
    assert fetched is not None
    assert fetched.title == "Order Book Dynamics"
    assert "order book microstructure" in fetched.queries_matched
    assert "market makers crypto" in fetched.queries_matched


def test_database_transcript_storage(temp_db: Database):
    video = VideoMetadata(
        video_id="vid_transcript_test",
        title="Order Book Dynamics",
        channel_id="chan_1",
        channel_title="Wintermute",
        url="https://youtube.com/watch?v=vid_transcript_test",
        topic_id="market-microstructure",
        duration_seconds=1200,
    )
    temp_db.upsert_video(video)

    seg1 = TranscriptSegment(start_seconds=0.0, end_seconds=15.5, text="Hello world", language="en")
    seg2 = TranscriptSegment(start_seconds=15.5, end_seconds=30.0, text="Order books explained", language="en")
    transcript = VideoTranscript(
        video_id="vid_transcript_test",
        language="en",
        segments=[seg1, seg2],
        full_raw_text="Hello world Order books explained",
        full_normalized_text="Hello world Order books explained",
        word_count=5,
        has_subtitles=True,
    )
    temp_db.save_transcript(transcript)

    saved = temp_db.get_transcript("vid_transcript_test")
    assert saved is not None
    assert len(saved.segments) == 2
    assert saved.segments[0].timestamp_formatted == "00:00"
    assert saved.segments[1].timestamp_formatted == "00:15"


def test_database_gatekeeper_evaluation(temp_db: Database):
    video = VideoMetadata(
        video_id="vid_eval_test",
        title="Funding Rate Masterclass",
        channel_id="chan_1",
        channel_title="Quant Desk",
        url="https://youtube.com/watch?v=vid_eval_test",
        topic_id="funding-rate-arbitrage",
        duration_seconds=1500,
    )
    temp_db.upsert_video(video)

    eval_res = GatekeeperEvaluation(
        relevance_score=8.5,
        technical_depth_score=8.0,
        practical_value_score=9.0,
        source_quality_score=7.5,
        commercial_noise_score=2.0,
        decision=GatekeeperVerdict.ACCEPT,
        reasons=["High technical depth", "Clear mathematical formulations"],
        uncertainties=[],
    )
    temp_db.save_gatekeeper_evaluation("vid_eval_test", eval_res)
    latest = temp_db.get_latest_evaluation("vid_eval_test", "gatekeeper")
    assert latest is not None
    assert latest["decision"] == "ACCEPT"
    assert latest["relevance_score"] == 8.5

"""Tests for Stage 2: Discovery, Deduplication, Ranking, and CSV Export."""

from pathlib import Path
import pytest
from research_academy.config import ScoringSettings
from research_academy.database import Database
from research_academy.models import DiscoveryStatus, VideoMetadata
from research_academy.pipeline.deduplication import Deduplicator
from research_academy.pipeline.ranking import VideoRanker
from research_academy.pipeline.publishing import Publisher
from research_academy.providers.mock_provider import MockYouTubeProvider


@pytest.fixture
def temp_db(tmp_path: Path) -> Database:
    db_file = tmp_path / "test.db"
    return Database(db_file)


def test_deduplication_aggregates_queries(temp_db: Database):
    dedup = Deduplicator(temp_db)
    v1 = VideoMetadata(
        video_id="vid_test_101",
        title="Microstructure of Limit Order Books",
        channel_id="chan_alpha",
        channel_title="Alpha Desk",
        url="https://youtube.com/watch?v=vid_test_101",
        topic_id="market-microstructure",
        duration_seconds=900,
    )

    # First encounter
    new_v, exist_v = dedup.process_candidates([v1], query_matched="order book mechanics")
    assert len(new_v) == 1
    assert len(exist_v) == 0
    assert "order book mechanics" in new_v[0].queries_matched

    # Second encounter via different query
    new_v2, exist_v2 = dedup.process_candidates([v1], query_matched="crypto market making wintermute")
    assert len(new_v2) == 0
    assert len(exist_v2) == 1
    assert "order book mechanics" in exist_v2[0].queries_matched
    assert "crypto market making wintermute" in exist_v2[0].queries_matched


def test_ranking_filters_scam_and_short_videos(temp_db: Database):
    settings = ScoringSettings()
    ranker = VideoRanker(settings, temp_db)

    good_video = VideoMetadata(
        video_id="good_01",
        title="Delta Neutral Hedging with Perpetual Futures",
        description="Comprehensive analysis of basis spread and liquidity management.",
        channel_id="chan_good",
        channel_title="Bell Curve",
        url="https://youtube.com/watch?v=good_01",
        topic_id="funding-rate-arbitrage",
        duration_seconds=1200,
        view_count=5000,
    )
    temp_db.upsert_video(good_video)

    short_video = VideoMetadata(
        video_id="short_02",
        title="Quick 2 minute crypto tip",
        description="Short teaser video",
        channel_id="chan_teaser",
        channel_title="Teaser Hub",
        url="https://youtube.com/watch?v=short_02",
        topic_id="funding-rate-arbitrage",
        duration_seconds=120,  # Below 420s
        view_count=20000,
    )
    temp_db.upsert_video(short_video)

    scam_video = VideoMetadata(
        video_id="scam_03",
        title="Связка дня на арбитраже: пассивный доход на автомате",
        description="Переходи в t.me/free_crypto_signals и получай бесплатная связка",
        channel_id="chan_scam",
        channel_title="Scam Signals",
        url="https://youtube.com/watch?v=scam_03",
        topic_id="02_arbitrage_types",
        duration_seconds=1500,
        view_count=10000,
    )
    temp_db.upsert_video(scam_video)

    accepted, rejected = ranker.rank_and_filter([good_video, short_video, scam_video])

    assert len(accepted) == 1
    assert accepted[0].video_id == "good_01"
    assert accepted[0].discovery_status == DiscoveryStatus.QUEUED_FOR_TRANSCRIPT

    assert len(rejected) == 2
    rej_ids = [r.video_id for r in rejected]
    assert "short_02" in rej_ids
    assert "scam_03" in rej_ids


def test_publisher_csv_export(temp_db: Database, tmp_path: Path):
    v = VideoMetadata(
        video_id="exp_01",
        title="Liquidity Pools AMM Mechanics",
        channel_id="chan_amm",
        channel_title="DeFi Academy",
        url="https://youtube.com/watch?v=exp_01",
        topic_id="onchain-dex-liquidity",
        duration_seconds=1000,
        view_count=12000,
        like_count=600,
    )
    v.calculate_derived_metrics()
    temp_db.upsert_video(v, query_matched="AMM liquidity pools")

    publisher = Publisher(temp_db, tmp_path)
    csv_file = publisher.export_csv("test_index.csv")

    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8")
    assert "exp_01" in content
    assert "Liquidity Pools AMM Mechanics" in content
    assert "AMM liquidity pools" in content

